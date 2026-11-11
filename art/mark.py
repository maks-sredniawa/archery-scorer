"""The mark: a tight group of three arrow holes inside a ring, the single definition of this app's identity.

See `art/README.md` for why it is the single source and where it came from.

Coordinates are in arbitrary units around an origin at the mark's centre; callers fit them to their
own canvas with `fit()`. y grows downward, as it does in both SVG and PIL.
"""

import re
from dataclasses import dataclass

GROUND = (0x10, 0x51, 0x32)
MARK_INK = (0xF7, 0xFA, 0xF6)


@dataclass(frozen=True)
class Subpath:
    """One closed contour, as cubic path data.

    `d` is always wound CLOCKWISE on screen (positive shoelace area with y downward). A hole is
    stored the same way and reversed at read time by `nodes()`, so it is subtracted by the non-zero
    fill rule that both SVG and VectorDrawable use by default. That is what makes the hole a real
    hole rather than a shape painted in the background colour — and it is why it survives the
    monochrome layer, where Android tints everything one flat colour and a painted hole would vanish.
    """

    d: str
    hole: bool = False


def circle(cx, cy, r):
    k = 0.5523 * r
    return (
        f"M{cx + r:g},{cy:g}"
        f"C{cx + r:g},{cy + k:g} {cx + k:g},{cy + r:g} {cx:g},{cy + r:g}"
        f"C{cx - k:g},{cy + r:g} {cx - r:g},{cy + k:g} {cx - r:g},{cy:g}"
        f"C{cx - r:g},{cy - k:g} {cx - k:g},{cy - r:g} {cx:g},{cy - r:g}"
        f"C{cx + k:g},{cy - r:g} {cx + r:g},{cy - k:g} {cx + r:g},{cy:g}"
        "Z"
    )


# Painted in this order: PIL rasterisers draw each part over the last, and the VectorDrawable's
# non-zero fill gives the same result from the windings.
PARTS = (
    Subpath(circle(0, 0, 25)),
    Subpath(circle(0, 0, 19.5), hole=True),
    Subpath(circle(0, 0, 16)),
    Subpath(circle(-4.5, -5.5, 3.7), hole=True),
    Subpath(circle(5, -3.5, 3.7), hole=True),
    Subpath(circle(0, 4.5, 3.7), hole=True),
)

_NUM = re.compile(r"-?\d*\.?\d+(?:e-?\d+)?")


def _points(d):
    """Path data -> the flat control-point list: 1 start point plus 3 per cubic segment."""
    pts = []
    for chunk in re.finditer(r"[MC]([^MCZz]*)", d):
        nums = [float(v) for v in _NUM.findall(chunk.group(1))]
        pts += list(zip(nums[0::2], nums[1::2]))
    return pts


def nodes(e, tf=lambda p: p):
    """Control points, caller-transformed, wound for fill or hole."""
    pts = _points(e.d)
    if e.hole:
        pts.reverse()
    return [tf(p) for p in pts]


def path_data(e, tf=lambda p: p, precision=2):
    """SVG/VectorDrawable path data for one subpath."""
    n = nodes(e, tf)

    def f(p):
        return f"{round(p[0], precision):g},{round(p[1], precision):g}"

    out = [f"M{f(n[0])}"]
    for i in range(1, len(n), 3):
        out.append("C" + " ".join(f(n[i + j]) for j in range(3)))
    return "".join(out) + "Z"


def outline(e, tf=lambda p: p, steps=32):
    """The same subpath flattened to a polygon, for renderers that can't draw curves."""
    n = nodes(e, tf)
    pts = []
    for i in range(1, len(n), 3):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = n[i - 1], n[i], n[i + 1], n[i + 2]
        for s in range(steps):
            t = s / steps
            u = 1 - t
            pts.append((
                u * u * u * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3,
                u * u * u * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3,
            ))
    return pts


def bounds(parts=PARTS):
    """Bounding box of the silhouette. Holes are ignored — a hole cannot extend the mark."""
    xs, ys = [], []
    for e in parts:
        if e.hole:
            continue
        for x, y in outline(e):
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def fit(canvas, art_size, parts=PARTS):
    """A transform placing the mark centred on a square canvas at a given longest-side size.

    Returns a function mapping mark coordinates to canvas coordinates.
    """
    x0, y0, x1, y1 = bounds(parts)
    scale = art_size / max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return lambda p: (canvas / 2 + (p[0] - cx) * scale, canvas / 2 + (p[1] - cy) * scale)
