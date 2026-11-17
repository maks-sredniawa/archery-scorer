"""Reading R4: find arrow shafts in one photo without clicks, on OpenCV's line segment detector alone."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np
from face import Face, FacePlane

PX_PER_MM = 1.6
MARGIN_RINGS = 3
PARALLEL_DEG = 6.0
WIDTH_RANGE = (0.6, 2.0)
JOIN_DEG = 4.0
JOIN_GAP_WIDTHS = 10.0
MIN_LENGTH_WIDTHS = 3.0
BESIDE_WIDTHS = 1.5
ARC_DEG = 15.0
OBLIQUE_DEG = 15.0
AWAY_FROM_FOOT_DEG = 30.0
MATCH_RINGS = 0.5


@dataclass
class Shaft:
    entry_mm: np.ndarray
    far_mm: np.ndarray


def face_to_image(plane: FacePlane) -> np.ndarray:
    return plane.k @ np.column_stack([plane.ex, plane.ey, plane.centre])


def rectify(image_bgr: np.ndarray, plane: FacePlane, extent_mm: float) -> tuple[np.ndarray, np.ndarray]:
    """Grey image of the face plane, x right and y up in face mm, centre in the middle."""
    size = round(2 * extent_mm * PX_PER_MM)
    px_to_mm = np.array([[1 / PX_PER_MM, 0, -extent_mm], [0, -1 / PX_PER_MM, extent_mm], [0, 0, 1]])
    to_image = face_to_image(plane) @ px_to_mm
    grey = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
    flat = cv2.warpPerspective(grey, to_image, (size, size), flags=cv2.WARP_INVERSE_MAP | cv2.INTER_AREA,
                               borderMode=cv2.BORDER_REPLICATE)
    return flat, px_to_mm


def side_contrast(grey: np.ndarray, a: np.ndarray, b: np.ndarray, normal: np.ndarray, offset: float = 2.0) -> float:
    """Mean brightness on the normal's side of a segment minus the other side."""
    t = np.linspace(0.1, 0.9, 9)[:, None]
    pts = a + t * (b - a)
    h, w = grey.shape

    def sample(p):
        x = np.clip(np.round(p[:, 0]).astype(int), 0, w - 1)
        y = np.clip(np.round(p[:, 1]).astype(int), 0, h - 1)
        return grey[y, x].astype(float)

    return float(np.mean(sample(pts + offset * normal) - sample(pts - offset * normal)))


def pair_edges(grey: np.ndarray, segments: np.ndarray, width_px: float) -> list[tuple[np.ndarray, np.ndarray, float]]:
    """A shaft shows two parallel edges about one shaft apart whose gradients face opposite ways; a ring edge
    shows one. Returns centrelines as (end, end, width)."""
    edges = []
    for x1, y1, x2, y2 in segments.reshape(-1, 4):
        a, b = np.array([x1, y1]), np.array([x2, y2])
        length = float(np.linalg.norm(b - a))
        if length < width_px:
            continue
        d = (b - a) / length
        n = np.array([-d[1], d[0]])
        edges.append((a, b, d, n, length, side_contrast(grey, a, b, n)))
    lo, hi = WIDTH_RANGE[0] * width_px, WIDTH_RANGE[1] * width_px
    cos_parallel = math.cos(math.radians(PARALLEL_DEG))
    found = []
    for i, (a1, b1, d1, n1, l1, c1) in enumerate(edges):
        for a2, b2, d2, n2, l2, c2 in edges[i + 1 :]:
            if abs(d1 @ d2) < cos_parallel:
                continue
            mid2 = (a2 + b2) / 2
            gap = (mid2 - a1) @ n1
            if not lo <= abs(gap) <= hi:
                continue
            along = sorted([(a2 - a1) @ d1, (b2 - a1) @ d1])
            overlap = min(l1, along[1]) - max(0.0, along[0])
            if overlap < 0.5 * min(l1, l2):
                continue
            towards_second = math.copysign(1.0, gap)
            facing_1 = c1 * towards_second
            facing_2 = (c2 * (n2 @ n1)) * -towards_second
            if facing_1 * facing_2 <= 0:
                continue
            start, end = max(0.0, along[0]), min(l1, along[1])
            centre_off = n1 * gap / 2
            found.append((a1 + d1 * start + centre_off, a1 + d1 * end + centre_off, abs(gap)))
    return found


def join(lines: list[tuple[np.ndarray, np.ndarray, float]], width_px: float) -> list[tuple[np.ndarray, np.ndarray]]:
    cos_join = math.cos(math.radians(JOIN_DEG))
    groups = [[a, b] for a, b, _ in lines]
    merged = True
    while merged:
        merged = False
        for i in range(len(groups)):
            for j in range(i + 1, len(groups)):
                a1, b1 = groups[i]
                a2, b2 = groups[j]
                d1 = (b1 - a1) / max(np.linalg.norm(b1 - a1), 1e-9)
                d2 = (b2 - a2) / max(np.linalg.norm(b2 - a2), 1e-9)
                if abs(d1 @ d2) < cos_join:
                    continue
                n1 = np.array([-d1[1], d1[0]])
                if max(abs((a2 - a1) @ n1), abs((b2 - a1) @ n1)) > width_px / 2:
                    continue
                t = sorted([0.0, float((b1 - a1) @ d1)] + [float((p - a1) @ d1) for p in (a2, b2)])
                span1 = sorted([0.0, float((b1 - a1) @ d1)])
                span2 = sorted([float((a2 - a1) @ d1), float((b2 - a1) @ d1)])
                gap = max(span1[0], span2[0]) - min(span1[1], span2[1])
                if gap > JOIN_GAP_WIDTHS * width_px:
                    continue
                groups[i] = [a1 + d1 * t[0], a1 + d1 * t[-1]]
                del groups[j]
                merged = True
                break
            if merged:
                break
    return [(a, b) for a, b in groups if np.linalg.norm(b - a) >= MIN_LENGTH_WIDTHS * width_px]


def drop_beside(lines: list[tuple[np.ndarray, np.ndarray]], width_px: float) -> list[tuple[np.ndarray, np.ndarray]]:
    """One shaft's edges also pair with its shadow or a neighbour's edge; keep the longest of parallel lines
    lying side by side."""
    cos_parallel = math.cos(math.radians(PARALLEL_DEG))
    kept = []
    for a, b in sorted(lines, key=lambda line: -np.linalg.norm(line[1] - line[0])):
        length = float(np.linalg.norm(b - a))
        d = (b - a) / length
        beside = False
        for ka, kb in kept:
            kd = (kb - ka) / np.linalg.norm(kb - ka)
            if abs(d @ kd) < cos_parallel:
                continue
            n = np.array([-kd[1], kd[0]])
            if abs(((a + b) / 2 - ka) @ n) > BESIDE_WIDTHS * width_px:
                continue
            along = sorted([float((a - ka) @ kd), float((b - ka) @ kd)])
            overlap = min(float(np.linalg.norm(kb - ka)), along[1]) - max(0.0, along[0])
            if overlap > 0.5 * length:
                beside = True
                break
        if not beside:
            kept.append((a, b))
    return kept


def runs_around_centre(a_mm: np.ndarray, b_mm: np.ndarray, face: Face) -> bool:
    mid = (a_mm + b_mm) / 2
    r = float(np.linalg.norm(mid))
    if not face.ring_mm < r < face.diameter_mm / 2 + face.ring_mm:
        return False
    d = (b_mm - a_mm) / max(np.linalg.norm(b_mm - a_mm), 1e-9)
    return abs(d @ (mid / r)) < math.sin(math.radians(ARC_DEG))


def against_the_view(a_mm: np.ndarray, b_mm: np.ndarray, camera: np.ndarray) -> bool:
    """Seen obliquely, a point off the face lands farther from the camera's foot the higher it is, so a shaft
    runs roughly away from that foot; a line across that direction lies in the face."""
    foot, height = camera[:2], camera[2]
    mid = (a_mm + b_mm) / 2
    if np.linalg.norm(mid - foot) < height * math.tan(math.radians(OBLIQUE_DEG)):
        return False
    d = (b_mm - a_mm) / max(np.linalg.norm(b_mm - a_mm), 1e-9)
    away = (mid - foot) / np.linalg.norm(mid - foot)
    return abs(d @ away) < math.cos(math.radians(AWAY_FROM_FOOT_DEG))


def find_shafts(image_bgr: np.ndarray, plane: FacePlane, face: Face, shaft_mm: float) -> list[Shaft]:
    extent = face.diameter_mm / 2 + MARGIN_RINGS * face.ring_mm
    grey, px_to_mm = rectify(image_bgr, plane, extent)
    segments = cv2.createLineSegmentDetector().detect(grey)[0]
    if segments is None:
        return []
    width_px = shaft_mm * PX_PER_MM
    camera = plane.camera_in_face()
    shafts = []
    for a, b in drop_beside(join(pair_edges(grey, segments, width_px), width_px), width_px):
        a_mm = (px_to_mm @ np.array([a[0], a[1], 1.0]))[:2]
        b_mm = (px_to_mm @ np.array([b[0], b[1], 1.0]))[:2]
        if runs_around_centre(a_mm, b_mm, face) or against_the_view(a_mm, b_mm, camera):
            continue
        foot = camera[:2]
        entry, far = (a_mm, b_mm) if np.linalg.norm(a_mm - foot) <= np.linalg.norm(b_mm - foot) else (b_mm, a_mm)
        if np.linalg.norm(entry) <= extent:
            shafts.append(Shaft(entry, far))
    return shafts


def match(found: list[np.ndarray], clicked: list[np.ndarray | None], within_mm: float) -> dict[int, tuple[int, float]]:
    """One to one, closest pair first. Returns clicked index → (found index, distance mm)."""
    pairs = sorted(
        (float(np.linalg.norm(f - c)), ci, fi)
        for ci, c in enumerate(clicked) if c is not None
        for fi, f in enumerate(found)
    )
    taken_c, taken_f, out = set(), set(), {}
    for dist, ci, fi in pairs:
        if dist > within_mm:
            break
        if ci in taken_c or fi in taken_f:
            continue
        taken_c.add(ci)
        taken_f.add(fi)
        out[ci] = (fi, dist)
    return out


def finds_its_shafts(found: int, clicked: int) -> bool:
    return 2 * found > clicked


def found_in_most_views(finds: list[bool]) -> bool:
    return 2 * sum(finds) > len(finds)
