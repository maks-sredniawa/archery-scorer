"""The mark: a fletched arrow stuck in the middle of a target face, the single definition of this app's identity.

See `art/README.md` for why it is the single source and where it came from.

Coordinates are in dp of a launcher icon's visible 72dp square, around an origin at its centre;
callers place that square on their own canvas with `fit()`. y grows downward, as it does in both SVG
and PIL. The face is drawn well past the square: it bleeds off every edge it touches, so it never
closes into a disc, and whatever shows it crops it.
"""

import math
import re
from dataclasses import dataclass

GROUND = (0x10, 0x51, 0x32)
FACE = (0x3F, 0x86, 0x60)
MARK_INK = (0xF7, 0xFA, 0xF6)

FRAME = 72


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


@dataclass(frozen=True)
class Layer:
    """Subpaths filled in one colour, minus `cut`.

    `cut` is one contour removed from this layer only, for a gap between it and a layer above; why it
    is not another hole is in `art/README.md`.
    """

    ink: tuple
    parts: tuple
    cut: Subpath | None = None


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


def _g(p):
    return f"{round(p[0], 3):g},{round(p[1], 3):g}"


def _line(a, b):
    return [((2 * a[0] + b[0]) / 3, (2 * a[1] + b[1]) / 3), ((a[0] + 2 * b[0]) / 3, (a[1] + 2 * b[1]) / 3), b]


def _arc(c, r, a0, a1):
    """Cubics along a circle from angle a0 to a1, at most a quarter turn each."""
    n = max(1, math.ceil(abs(a1 - a0) / (math.pi / 2)))
    step = (a1 - a0) / n
    k = 4 / 3 * math.tan(step / 4) * r
    out = []
    for i in range(n):
        s, e = a0 + i * step, a0 + (i + 1) * step
        out += [
            (c[0] + r * math.cos(s) - k * math.sin(s), c[1] + r * math.sin(s) + k * math.cos(s)),
            (c[0] + r * math.cos(e) + k * math.sin(e), c[1] + r * math.sin(e) - k * math.cos(e)),
            (c[0] + r * math.cos(e), c[1] + r * math.sin(e)),
        ]
    return out


def _cubics(start, ctrl):
    return f"M{_g(start)}" + "".join("C" + " ".join(_g(p) for p in ctrl[i:i + 3]) for i in range(0, len(ctrl), 3)) + "Z"


def polygon(pts, grow=0.0):
    """A clockwise polygon as cubic path data, optionally grown outward with round corners.

    Growing intersects neighbouring offset edges at a concave corner and rounds a convex one, which
    is right as long as no edge is shorter than the growth eats from it — true of the arrow here.
    """
    n = len(pts)
    if not grow:
        ctrl = []
        for i in range(n):
            ctrl += _line(pts[i], pts[(i + 1) % n])
        return _cubics(pts[0], ctrl)

    def outward(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = math.hypot(dx, dy)
        return dy / length, -dx / length

    joins = []
    for i in range(n):
        prev, p, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        n0, n1 = outward(prev, p), outward(p, nxt)
        turn = (p[0] - prev[0]) * (nxt[1] - p[1]) - (p[1] - prev[1]) * (nxt[0] - p[0])
        if turn > 0:
            a0, a1 = math.atan2(n0[1], n0[0]), math.atan2(n1[1], n1[0])
            while a1 < a0:
                a1 += 2 * math.pi
            joins.append(("arc", p, a0, a1))
        else:
            bx, by = n0[0] + n1[0], n0[1] + n1[1]
            k = grow / (1 + n0[0] * n1[0] + n0[1] * n1[1])
            joins.append(("pt", (p[0] + bx * k, p[1] + by * k)))

    def ends(j):
        if j[0] == "pt":
            return j[1], j[1]
        _, c, a0, a1 = j
        return (c[0] + grow * math.cos(a0), c[1] + grow * math.sin(a0)), (c[0] + grow * math.cos(a1), c[1] + grow * math.sin(a1))

    start = ends(joins[0])[1]
    ctrl = []
    for i in range(1, n + 1):
        j = joins[i % n]
        ctrl += _line(ctrl[-1] if ctrl else start, ends(j)[0])
        if j[0] == "arc":
            ctrl += _arc(j[1], grow, j[2], j[3])
    return _cubics(start, ctrl)


def _place(points, tail, tip):
    """Arrow-local points (x along the shaft from the nock, y across it) -> mark coordinates."""
    a = math.atan2(tip[1] - tail[1], tip[0] - tail[0])
    c, s = math.cos(a), math.sin(a)
    return [(tail[0] + x * c - y * s, tail[1] + x * s + y * c) for x, y in points]


def _arrow(tail, tip, shaft=5.0, vane_at=1.0, vane_len=14.0, vane_high=6.5, sweep=6.0, lead=6.0):
    """The arrow's silhouette as one clockwise outline: shaft and both vanes, nock at `tail`.

    Each vane is a parallelogram swept back towards the nock (`sweep` and `lead` equal): at 48px a
    vane is three or four pixels, and two clear parallel slants are what still read as feathers
    there, where a long shallow leading edge blurred the pair into one blob.
    """
    length = math.dist(tail, tip)
    h = shaft / 2
    v0, v1 = vane_at + sweep, vane_at + sweep + vane_len
    top = [(v0, -h), (v0 - sweep, -h - vane_high), (v1 - lead, -h - vane_high), (v1, -h)]
    local = [(0, -h), *top, (length, -h), (length, h), *[(x, -y) for x, y in reversed(top)], (0, h)]
    return _place(local, tail, tip)


FACE_CENTRE = (-13, 13)
TAIL, TIP = (24.5, -17), (-9.5, 10)
KEYLINE = 2.6

_ARROW = _arrow(TAIL, TIP)

# The arrow alone, all the flat-tinted layers (monochrome, notification) carry.
ARROW = (Subpath(polygon(_ARROW)),)

LAYERS = (
    Layer(
        FACE,
        tuple(Subpath(circle(*FACE_CENTRE, r), hole=i % 2 == 1) for i, r in enumerate((52, 41, 30, 19, 8))),
        cut=Subpath(polygon(_ARROW, grow=KEYLINE)),
    ),
    Layer(MARK_INK, ARROW),
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


def bounds(parts):
    """Bounding box of a silhouette. Holes are ignored — a hole cannot extend the mark."""
    xs, ys = [], []
    for e in parts:
        if e.hole:
            continue
        for x, y in outline(e):
            xs.append(x)
            ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


def fit(canvas, frame_size):
    """A transform putting the mark's FRAME square, centred, `frame_size` across on a square canvas."""
    k = frame_size / FRAME
    return lambda p: (canvas / 2 + p[0] * k, canvas / 2 + p[1] * k)


def fit_bounds(canvas, art_size, parts):
    """A transform centring `parts` alone on a square canvas at a given longest-side size."""
    x0, y0, x1, y1 = bounds(parts)
    k = art_size / max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return lambda p: (canvas / 2 + (p[0] - cx) * k, canvas / 2 + (p[1] - cy) * k)
