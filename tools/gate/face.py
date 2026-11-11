"""Face geometry, ring fitting, plane recovery and scoring shared by the Phase 0 gate scripts."""

from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Face:
    diameter_mm: float = 400.0
    line_mm: float = 1.0

    @property
    def ring_mm(self) -> float:
        return self.diameter_mm / 20.0

    def zone_outer_mm(self, zone: int) -> float:
        return (11 - zone) * self.ring_mm

    def fitted_boundaries(self) -> dict[str, float]:
        """Radius at which each colour region visibly ends: a dividing line sits inside the higher zone."""
        w = self.ring_mm
        return {"gold": 2 * w - self.line_mm, "red": 4 * w - self.line_mm, "blue": 6 * w}


def score(face: Face, centre_distance_mm: float, shaft_mm: float) -> int:
    """World Archery Book 3 Art. 12.2: a shaft touching a line scores the higher zone."""
    edge = centre_distance_mm - shaft_mm / 2.0
    if edge <= 0:
        return 10
    zone = 11 - math.ceil(edge / face.ring_mm - 1e-9)
    return zone if zone >= 1 else 0


def near_line(face: Face, centre_distance_mm: float, shaft_mm: float, margin_mm: float = 2.0) -> bool:
    edge = centre_distance_mm - shaft_mm / 2.0
    nearest = round(edge / face.ring_mm) * face.ring_mm
    return nearest > 0 and abs(edge - nearest) < margin_mm


def lab_masks(image_bgr: np.ndarray) -> dict[str, np.ndarray]:
    lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
    lum, a, b = lab[..., 0].astype(int), lab[..., 1].astype(int), lab[..., 2].astype(int)
    gold = (b > 180) & (a < 145)
    red = (a > 165) & (b < 180)
    blue = (b < 105) & (lum > 120)
    return {
        "gold": gold,
        "red": gold | red,
        "blue": gold | red | blue,
    }


def region_boundary(mask: np.ndarray, inside: np.ndarray | None = None) -> np.ndarray | None:
    m = mask.astype(np.uint8) * 255
    if inside is not None:
        m &= inside
    k = max(3, int(round(min(m.shape) / 300)) | 1)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k)))
    count, labels, stats, _ = cv2.connectedComponentsWithStats(m)
    if count < 2:
        return None
    biggest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    m = np.where(labels == biggest, 255, 0).astype(np.uint8)
    contours, _ = cv2.findContours(m, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    contour = max(contours, key=cv2.contourArea)
    hull = cv2.convexHull(contour)
    pts = contour.reshape(-1, 2).astype(np.float64)
    on_hull = np.array([cv2.pointPolygonTest(hull, (float(x), float(y)), True) < 1.5 for x, y in pts])
    pts = pts[on_hull]
    return pts if len(pts) >= 20 else None


def ellipse_region(shape, ellipse) -> np.ndarray:
    region = np.zeros(shape[:2], np.uint8)
    cv2.ellipse(region, ellipse, 255, -1)
    return region


def ellipse_conic(ellipse) -> np.ndarray:
    (cx, cy), (w, h), angle = ellipse
    a, b = w / 2.0, h / 2.0
    t = math.radians(angle)
    rot = np.array([[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]])
    inner = rot @ np.diag([1 / a**2, 1 / b**2]) @ rot.T
    c = np.array([cx, cy])
    conic = np.zeros((3, 3))
    conic[:2, :2] = inner
    conic[:2, 2] = conic[2, :2] = -inner @ c
    conic[2, 2] = c @ inner @ c - 1.0
    return conic


def conic_residual_px(conic: np.ndarray, pts: np.ndarray) -> np.ndarray:
    """Approximate geometric distance: algebraic distance over the gradient's length."""
    h = np.hstack([pts, np.ones((len(pts), 1))])
    alg = np.einsum("ni,ij,nj->n", h, conic, h)
    grad = 2 * (h @ conic)[:, :2]
    return np.abs(alg) / np.maximum(np.linalg.norm(grad, axis=1), 1e-12)


def robust_ellipse(pts: np.ndarray, rounds: int = 3, keep_px: float = 2.5):
    keep = pts
    for _ in range(rounds):
        ellipse = cv2.fitEllipse(keep.astype(np.float32))
        resid = conic_residual_px(ellipse_conic(ellipse), pts)
        keep = pts[resid < keep_px]
        if len(keep) < 20:
            break
    return ellipse, keep


@dataclass
class FacePlane:
    """The face plane seen from one camera, with an in-plane frame anchored on a reference point."""

    k: np.ndarray
    normal: np.ndarray
    centre: np.ndarray
    ex: np.ndarray
    ey: np.ndarray

    def ray(self, px) -> np.ndarray:
        return np.linalg.solve(self.k, np.array([px[0], px[1], 1.0]))

    def to_plane(self, px) -> np.ndarray:
        r = self.ray(px)
        return r * (self.normal @ self.centre) / (self.normal @ r)

    def to_face(self, px) -> np.ndarray:
        d = self.to_plane(px) - self.centre
        return np.array([self.ex @ d, self.ey @ d])

    def rotation(self) -> np.ndarray:
        return np.vstack([self.ex, self.ey, self.normal])

    def camera_in_face(self) -> np.ndarray:
        return self.rotation() @ (-self.centre)

    def dir_in_face(self, px) -> np.ndarray:
        return self.rotation() @ self.ray(px)


def intrinsics(f_px: float, width: int, height: int) -> np.ndarray:
    return np.array([[f_px, 0, width / 2.0], [0, f_px, height / 2.0], [0, 0, 1.0]])


def centre_and_horizon(inner: np.ndarray, outer: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Concentric circles: the pencil's lone eigenvector is the imaged centre, its polar the vanishing line."""
    vals, vecs = np.linalg.eig(np.linalg.solve(outer, inner))
    vals = vals.real
    spread = [abs(vals[i] - vals[(i + 1) % 3]) + abs(vals[i] - vals[(i + 2) % 3]) for i in range(3)]
    c = vecs[:, int(np.argmax(spread))].real
    c = c / c[2]
    horizon = inner @ c
    return c, horizon / np.linalg.norm(horizon[:2])


@dataclass
class RingFit:
    plane: FacePlane | None
    residual_mm: dict[str, float]
    reason: str = ""


def fit_rings(image_bgr: np.ndarray, f_px: float, face: Face, ref_px) -> RingFit:
    h, w = image_bgr.shape[:2]
    k = intrinsics(f_px, w, h)
    masks = lab_masks(image_bgr)
    radii = face.fitted_boundaries()
    fits, points, ellipses = {}, {}, {}
    inside = None
    for name in ("blue", "red", "gold"):
        pts = region_boundary(masks[name], inside)
        if pts is None:
            if name == "gold":
                break
            return RingFit(None, {}, f"no {name} region found")
        ellipse, kept = robust_ellipse(pts)
        fits[name], points[name], ellipses[name] = ellipse_conic(ellipse), kept, ellipse
        inside = ellipse_region(image_bgr.shape, ellipse)

    c, horizon = centre_and_horizon(fits["red"], fits["blue"])
    normal = k.T @ horizon
    normal /= np.linalg.norm(normal)
    d = np.linalg.solve(k, c)
    if normal @ d > 0:
        normal = -normal

    scales = []
    for name in ("red", "blue"):
        pts = points[name]
        for x, y in pts:
            r = np.linalg.solve(k, np.array([x, y, 1.0]))
            gap = np.linalg.norm(r * (normal @ d) / (normal @ r) - d)
            scales.append(radii[name] / gap)
    centre = d * float(np.median(scales))

    plane = FacePlane(k, normal, centre, np.zeros(3), np.zeros(3))
    toward_ref = plane.to_plane(ref_px) - centre
    ex = toward_ref - (toward_ref @ normal) * normal
    plane.ex = ex / np.linalg.norm(ex)
    plane.ey = np.cross(normal, plane.ex)

    residual = {"gold": float("nan")}
    for name, pts in points.items():
        dist = np.array([np.linalg.norm(plane.to_face(p)) for p in pts])
        residual[name] = float(np.sqrt(np.mean((dist - radii[name]) ** 2)))
    return RingFit(plane, residual)


def single_view_entry(plane: FacePlane, near_px) -> np.ndarray:
    return plane.to_face(near_px)


def triangulated_entry(shafts: list[tuple[FacePlane, tuple, tuple]]) -> tuple[np.ndarray, float]:
    """Each view's shaft spans a plane through its camera; every such plane meets the face in a line
    through the entry point. Returns the least-squares meeting point and the widest angle between lines."""
    rows, rhs, normals = [], [], []
    for plane, near, far in shafts:
        cam = plane.camera_in_face()
        m = np.cross(plane.dir_in_face(near), plane.dir_in_face(far))
        ab = m[:2]
        scale = np.linalg.norm(ab)
        rows.append(ab / scale)
        rhs.append((m @ cam) / scale)
        normals.append(ab / scale)
    point, *_ = np.linalg.lstsq(np.array(rows), np.array(rhs), rcond=None)
    widest = 0.0
    for i in range(len(normals)):
        for j in range(i + 1, len(normals)):
            cos = abs(float(normals[i] @ normals[j]))
            widest = max(widest, math.degrees(math.acos(min(1.0, cos))))
    return point, widest
