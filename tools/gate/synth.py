#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["opencv-python-headless>=4.10", "numpy>=1.26"]
# ///
"""Render a fake end with known arrow positions, so gate.py can be checked before real photos exist.

    uv run --script tools/gate/synth.py OUT_DIR

Writes three views, a straight-on photo of the holes, clicks.json (the points a person would click,
with 1 px of noise) and truth.json (where every arrow really entered).
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from face import Face  # noqa: E402

WIDTH, HEIGHT, F_PX = 3000, 2250, 2600.0
PX_PER_MM = 4.0
TEXTURE_HALF_MM = 300.0
PAPER_HALF_MM = 210.0
REFERENCE_MM = (-PAPER_HALF_MM, PAPER_HALF_MM)
SHAFT_MM = 5.5

GOLD, RED, BLUE, BLACK, WHITE = (82, 229, 255), (88, 80, 246), (228, 180, 0), (25, 25, 25), (250, 250, 250)
STRAW = (115, 170, 200)
ZONE_COLOUR = {10: GOLD, 9: GOLD, 8: RED, 7: RED, 6: BLUE, 5: BLUE, 4: BLACK, 3: BLACK, 2: WHITE, 1: WHITE}
NO_LINE_ZONES = {5, 3}


def to_tex(x_mm: float, y_mm: float) -> tuple[float, float]:
    return (x_mm + TEXTURE_HALF_MM) * PX_PER_MM, (TEXTURE_HALF_MM - y_mm) * PX_PER_MM


def face_texture(face: Face) -> np.ndarray:
    size = int(2 * TEXTURE_HALF_MM * PX_PER_MM)
    tex = np.full((size, size, 3), STRAW, np.uint8)
    corner_a = tuple(int(v) for v in to_tex(-PAPER_HALF_MM, PAPER_HALF_MM))
    corner_b = tuple(int(v) for v in to_tex(PAPER_HALF_MM, -PAPER_HALF_MM))
    cv2.rectangle(tex, corner_a, corner_b, WHITE, -1)
    centre = tuple(int(v) for v in to_tex(0, 0))
    line_px = max(1, int(round(face.line_mm * PX_PER_MM)))
    for zone in range(1, 11):
        r_px = face.zone_outer_mm(zone) * PX_PER_MM
        cv2.circle(tex, centre, int(round(r_px)), ZONE_COLOUR[zone], -1, cv2.LINE_AA)
        if zone not in NO_LINE_ZONES:
            line_colour = WHITE if ZONE_COLOUR[zone] == BLACK else BLACK
            cv2.circle(tex, centre, int(round(r_px - line_px / 2)), line_colour, line_px, cv2.LINE_AA)
    cv2.circle(tex, centre, int(round(face.ring_mm / 2 * PX_PER_MM)), BLACK, 1, cv2.LINE_AA)
    return tex


def camera(yaw_deg: float, pitch_deg: float, roll_deg: float, distance_mm: float):
    yaw, pitch = math.radians(yaw_deg), math.radians(pitch_deg)
    pos = distance_mm * np.array([math.sin(yaw) * math.cos(pitch), math.sin(pitch), math.cos(yaw) * math.cos(pitch)])
    z = -pos / np.linalg.norm(pos)
    x = np.cross(z, [0.0, 1.0, 0.0])
    x /= np.linalg.norm(x)
    y = np.cross(z, x)
    r = np.vstack([x, y, z])
    roll = math.radians(roll_deg)
    spin = np.array([[math.cos(roll), -math.sin(roll), 0], [math.sin(roll), math.cos(roll), 0], [0, 0, 1]])
    r = spin @ r
    return r, -r @ pos


def project(k, r, t, pts3: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    cam = (r @ pts3.T).T + t
    uv = (k @ cam.T).T
    return uv[:, :2] / uv[:, 2:3], cam[:, 2]


def arrows(face: Face) -> list[dict]:
    w = face.ring_mm
    entries = [
        (0.0, w * 2 + SHAFT_MM / 2 - 0.4),
        (w * 3 + SHAFT_MM / 2 + 0.3, 0.0),
        (-14.0, -9.0),
        (-8.0, -15.5),
        (-19.0, -16.0),
        (35.0, 52.0),
    ]
    tilts = [(0.05, -0.08), (-0.10, 0.04), (0.12, 0.10), (-0.06, -0.12), (0.02, 0.15), (0.09, -0.03)]
    vanes = [(0, 140, 255), (40, 200, 40), (0, 140, 255), (220, 220, 220), (40, 200, 40), (0, 140, 255)]
    out = []
    for (x, y), (tx, ty), vane in zip(entries, tilts, vanes):
        v = np.array([tx, ty, 1.0])
        out.append({"entry": np.array([x, y, 0.0]), "dir": v / np.linalg.norm(v), "vane": vane})
    return out


def render(tex: np.ndarray, k, r, t, shafts: list[dict], rng) -> np.ndarray:
    plane_to_img = k @ np.column_stack([r[:, 0], r[:, 1], t])
    tex_to_plane = np.array(
        [[1 / PX_PER_MM, 0, -TEXTURE_HALF_MM], [0, -1 / PX_PER_MM, TEXTURE_HALF_MM], [0, 0, 1]]
    )
    img = cv2.warpPerspective(tex, plane_to_img @ tex_to_plane, (WIDTH, HEIGHT), borderValue=STRAW)
    depth_sorted = sorted(shafts, key=lambda a: -project(k, r, t, a["entry"][None])[1][0])
    for arrow in depth_sorted:
        length = np.linspace(0, 320, 40)
        pts3 = arrow["entry"][None] + length[:, None] * arrow["dir"][None]
        uv, depth = project(k, r, t, pts3)
        for i in range(len(uv) - 1):
            thick = max(2, int(round(SHAFT_MM * F_PX / depth[i])))
            colour = arrow["vane"] if length[i] > 240 else (30, 30, 30)
            if length[i] > 240:
                thick *= 4
            cv2.line(img, tuple(np.round(uv[i]).astype(int)), tuple(np.round(uv[i + 1]).astype(int)), colour, thick, cv2.LINE_AA)
    shade = np.linspace(0.85, 1.05, WIDTH)[None, :, None]
    img = np.clip(img.astype(np.float32) * shade + rng.normal(0, 3, img.shape), 0, 255).astype(np.uint8)
    return cv2.GaussianBlur(img, (3, 3), 0)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("out", type=Path)
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    face = Face()
    tex = face_texture(face)
    k = np.array([[F_PX, 0, WIDTH / 2], [0, F_PX, HEIGHT / 2], [0, 0, 1]])
    shafts = arrows(face)
    reference = np.array([*REFERENCE_MM, 0.0])

    def jitter(p):
        return [float(v) for v in p + rng.normal(0, 1.0, 2)]

    clicks = {"face_mm": face.diameter_mm, "line_mm": face.line_mm, "shaft_mm": SHAFT_MM, "views": []}
    for name, (yaw, pitch, roll, dist) in {
        "front": (0, 3, 1.5, 1000),
        "left": (-35, 5, -2.0, 1050),
        "right": (35, 2, 2.5, 980),
    }.items():
        r, t = camera(yaw, pitch, roll, dist)
        cv2.imwrite(str(args.out / f"{name}.jpg"), render(tex, k, r, t, shafts, rng), [cv2.IMWRITE_JPEG_QUALITY, 92])
        view = {"image": f"{name}.jpg", "f_px": F_PX, "ref": jitter(project(k, r, t, reference[None])[0][0]), "arrows": []}
        for arrow in shafts:
            near, far = arrow["entry"] + 12 * arrow["dir"], arrow["entry"] + 200 * arrow["dir"]
            uv, _ = project(k, r, t, np.vstack([near, far]))
            view["arrows"].append({"near": jitter(uv[0]), "far": jitter(uv[1])})
        clicks["views"].append(view)

    holes_tex = tex.copy()
    for arrow in shafts:
        centre = tuple(int(round(v)) for v in to_tex(*arrow["entry"][:2]))
        cv2.circle(holes_tex, centre, int(round(SHAFT_MM / 2 * PX_PER_MM)), (20, 30, 45), -1, cv2.LINE_AA)
    r, t = camera(0, 1, 0.5, 900)
    cv2.imwrite(str(args.out / "holes.jpg"), render(holes_tex, k, r, t, [], rng), [cv2.IMWRITE_JPEG_QUALITY, 92])
    holes_uv, _ = project(k, r, t, np.vstack([a["entry"] for a in shafts]))
    clicks["holes"] = {
        "image": "holes.jpg",
        "f_px": F_PX,
        "ref": jitter(project(k, r, t, reference[None])[0][0]),
        "arrows": [jitter(p) for p in holes_uv],
    }

    ref_angle = math.atan2(REFERENCE_MM[1], REFERENCE_MM[0])
    c, s = math.cos(-ref_angle), math.sin(-ref_angle)
    truth = [[c * a["entry"][0] - s * a["entry"][1], s * a["entry"][0] + c * a["entry"][1]] for a in shafts]
    (args.out / "clicks.json").write_text(json.dumps(clicks, indent=2))
    (args.out / "truth.json").write_text(json.dumps({"entries_face_mm": truth}, indent=2))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
