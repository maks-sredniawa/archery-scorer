#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["opencv-python-headless>=4.10", "numpy>=1.26", "pillow>=10", "rich>=13"]
# ///
"""Phase 0's gate (docs/phase-0.md, section 1): score one photographed end against the holes it left.

    uv run --script tools/gate/gate.py RUN_DIR

RUN_DIR holds the photos and clicks.json, written by click.py (or synth.py for a fake end). Prints
readings R1 to R4 and writes report.json beside them, with each view's automatic shafts drawn on
<view>-shafts.png.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

sys.path.insert(0, str(Path(__file__).resolve().parent))
from face import Face, RingFit, fit_rings, near_line, score, single_view_entry, triangulated_entry  # noqa: E402
from shafts import MATCH_RINGS, Shaft, face_to_image, find_shafts, match  # noqa: E402

PASS_MEDIAN_MM = 1.5
RING_FIT_MAX_RMS_MM = 1.0
console = Console()


def focal_px(path: Path, entry: dict) -> float:
    if "f_px" in entry:
        return float(entry["f_px"])
    with Image.open(path) as img:
        exif = img.getexif().get_ifd(0x8769)
        f35 = exif.get(0xA405)
        if not f35:
            raise SystemExit(f"{path.name}: no 35 mm focal length in EXIF; add \"f_px\" to its entry in clicks.json")
        width, height = img.size
    return float(f35) * float(np.hypot(width, height)) / float(np.hypot(36, 24))


def load(run: Path, entry: dict) -> np.ndarray:
    path = run / entry["image"]
    image = cv2.imread(str(path))
    if image is None:
        raise SystemExit(f"cannot read {path}")
    return image


def ring_fit(run: Path, image: np.ndarray, entry: dict, face: Face, label: str) -> RingFit:
    with console.status(f"fitting rings in {label} ..."):
        return fit_rings(image, focal_px(run / entry["image"], entry), face, entry["ref"])


def draw_shafts(path: Path, image: np.ndarray, plane, shafts: list[Shaft], matched: dict) -> None:
    to_image = face_to_image(plane)

    def px(p_mm):
        q = to_image @ np.array([p_mm[0], p_mm[1], 1.0])
        return tuple(int(round(v)) for v in q[:2] / q[2])

    found = {fi for fi, _ in matched.values()}
    out = image.copy()
    thick = max(2, image.shape[1] // 600)
    for fi, shaft in enumerate(shafts):
        colour = (0, 200, 0) if fi in found else (0, 0, 255)
        cv2.line(out, px(shaft.entry_mm), px(shaft.far_mm), colour, thick, cv2.LINE_AA)
        cv2.circle(out, px(shaft.entry_mm), 4 * thick, colour, -1, cv2.LINE_AA)
    cv2.imwrite(str(path), out)


def shafts_reading(run: Path, clicks: dict, images: list, planes: list, holes: list, face: Face, shaft: float):
    """R4: per view, the clicked arrows whose hole an automatic entry lands within half a ring width of.
    Holes rather than near clicks, because a near click may sit up the shaft or on a hidden entry."""
    table = Table(title=f"R4 · shafts found automatically (entry within {MATCH_RINGS} ring width of the hole)")
    for col in ("view", "clicked", "found", "missed", "false", "entry to hole"):
        table.add_column(col)
    views, finding = [], 0
    for view, image, plane in zip(clicks["views"], images, planes):
        clicked = [hole if arrow is not None else None for hole, arrow in zip(holes, view["arrows"])]
        count = sum(c is not None for c in clicked)
        if plane is None:
            table.add_row(view["image"], str(count), "-", "-", "-", "no ring fit")
            views.append({"image": view["image"], "clicked": count, "found": 0, "false": None, "entry_to_hole_mm": []})
            continue
        with console.status(f"finding shafts in {view['image']} ..."):
            found = find_shafts(image, plane, face, shaft)
        matched = match([s.entry_mm for s in found], clicked, MATCH_RINGS * face.ring_mm)
        draw_shafts(run / f"{Path(view['image']).stem}-shafts.png", image, plane, found, matched)
        errors = [matched[i][1] for i in sorted(matched)]
        finding += len(matched) * 2 > count
        table.add_row(view["image"], str(count), str(len(matched)), str(count - len(matched)),
                      str(len(found) - len(matched)), summary(errors))
        views.append({"image": view["image"], "clicked": count, "found": len(matched),
                      "false": len(found) - len(matched),
                      "entry_to_hole_mm": {str(i + 1): d for i, (_, d) in sorted(matched.items())}})
    console.print(table)
    return {"views": views, "found_in_most_views": finding * 2 > len(views)}


def fits(fit: RingFit) -> bool:
    return fit.plane is not None and max(fit.residual_mm["red"], fit.residual_mm["blue"]) <= RING_FIT_MAX_RMS_MM


def median_or_none(errors: list[float]) -> float | None:
    return statistics.median(errors) if errors else None


def summary(errors: list[float]) -> str:
    if not errors:
        return "none"
    return f"median {statistics.median(errors):.2f} mm, worst {max(errors):.2f} mm ({len(errors)})"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    clicks_path, report_path = args.run / "clicks.json", args.run / "report.json"
    if not clicks_path.is_file():
        raise SystemExit(f"no {clicks_path}: run click.py (or synth.py) on this folder first")
    report_path.unlink(missing_ok=True)
    clicks = json.loads(clicks_path.read_text())
    face = Face(clicks.get("face_mm", 400.0), clicks.get("line_mm", 1.0))
    shaft = float(clicks["shaft_mm"])
    console.print(Panel(f"Phase 0 gate · {args.run} · {face.diameter_mm / 10:.0f} cm face · shaft {shaft} mm", expand=False))

    rings = Table(title=f"R1 · ring fit per photo (RMS distance from the nominal edge, mm; fits ≤ {RING_FIT_MAX_RMS_MM})")
    for col in ("photo", "gold", "red", "blue", "fits"):
        rings.add_column(col)
    planes, fitted = [], []
    labelled = [(v["image"], v) for v in clicks["views"]] + [(clicks["holes"]["image"] + " (holes)", clicks["holes"])]
    images = []
    for label, entry in labelled:
        image = load(args.run, entry)
        images.append(image)
        fit = ring_fit(args.run, image, entry, face, label)
        ok = fits(fit)
        fitted.append(ok)
        cells = [f"{fit.residual_mm[n]:.2f}" for n in ("gold", "red", "blue")] if fit.plane else ["-"] * 3
        rings.add_row(label, *cells, "yes" if ok else fit.reason or "no")
        planes.append(fit.plane)
    console.print(rings)
    view_planes, holes_plane = planes[:-1], planes[-1]
    views_fit, holes_fit = all(fitted[:-1]), fitted[-1]
    if holes_plane is None or not any(view_planes):
        reason = "rings found in no view" if holes_fit else "NO READING: retake the holes photo"
        console.print(f"[red]{reason}; no entry point can be computed.[/red]")
        passed = False if holes_fit else None
        report_path.write_text(json.dumps({"passed": passed, "rings_fit": views_fit, "holes_fit": holes_fit,
                                           "reason": reason}, indent=2))
        raise SystemExit(1)

    holes = [holes_plane.to_face(p) for p in clicks["holes"]["arrows"]]
    table = Table(title="R2 · entry point against the hole, mm")
    for col in ("arrow", "hole", "seen in", "front only", "two views", "angle", "score: hole / two views", "check"):
        table.add_column(col)
    single_err, multi_err, rows = {False: [], True: []}, [], []
    for i, hole in enumerate(holes):
        seen = [
            (plane, view["arrows"][i]["near"], view["arrows"][i]["far"])
            for plane, view in zip(view_planes, clicks["views"])
            if plane is not None and view["arrows"][i] is not None
        ]
        front = clicks["views"][0]["arrows"][i]
        single = single_view_entry(view_planes[0], front["near"]) if view_planes[0] and front else None
        front_hidden = bool(front.get("near_hidden")) if front else None
        multi, angle = triangulated_entry(seen) if len(seen) >= 2 else (None, 0.0)
        s_err = float(np.linalg.norm(single - hole)) if single is not None else None
        m_err = float(np.linalg.norm(multi - hole)) if multi is not None else None
        if s_err is not None:
            single_err[front_hidden].append(s_err)
        if m_err is not None:
            multi_err.append(m_err)
        hole_r = float(np.linalg.norm(hole))
        est_score = score(face, float(np.linalg.norm(multi)), shaft) if multi is not None else None
        flag = "near a line" if near_line(face, hole_r, shaft) else ""
        table.add_row(
            str(i + 1),
            f"({hole[0]:.1f}, {hole[1]:.1f})",
            str(len(seen)),
            f"{s_err:.2f}{' (hidden)' if front_hidden else ''}" if s_err is not None else "-",
            f"{m_err:.2f}" if m_err is not None else "-",
            f"{angle:.0f}°",
            f"{score(face, hole_r, shaft)} / {est_score if est_score is not None else '-'}",
            flag,
        )
        rows.append({"arrow": i + 1, "hole_mm": hole.tolist(), "views": len(seen), "front_only_mm": s_err,
                     "front_entry_hidden": front_hidden,
                     "two_view_mm": m_err, "angle_deg": angle, "hole_score": score(face, hole_r, shaft),
                     "two_view_score": est_score})
    console.print(table)

    hiding = Table(title="R3 · entry points each view hides")
    for col in ("view", "arrows seen", "entry hidden"):
        hiding.add_column(col)
    views = []
    for view in clicks["views"]:
        seen = [a for a in view["arrows"] if a is not None]
        hidden = sum(bool(a.get("near_hidden")) for a in seen)
        hiding.add_row(view["image"], str(len(seen)), str(hidden))
        views.append({"image": view["image"], "seen": len(seen), "entry_hidden": hidden})
    console.print(hiding)

    shafts = shafts_reading(args.run, clicks, images[:-1], view_planes, holes, face, shaft)

    front_all = single_err[False] + single_err[True]
    median_multi = statistics.median(multi_err) if multi_err else float("inf")
    median_single = statistics.median(front_all) if front_all else float("inf")
    passed = views_fit and median_multi <= PASS_MEDIAN_MM
    verdict = ("PASS" if passed else "FAIL") if holes_fit else "NO READING: retake the holes photo"
    console.print(
        Panel(
            f"rings fit in all {len(view_planes)} views: {'yes' if views_fit else 'no'}\n"
            f"rings fit in the holes photo (ground truth usable): {'yes' if holes_fit else 'no'}\n"
            f"front photo only: median {median_single:.2f} mm, worst {max(front_all, default=float('nan')):.2f} mm\n"
            f"  entry visible: {summary(single_err[False])}\n"
            f"  entry hidden: {summary(single_err[True])}\n"
            f"two or more views: median {median_multi:.2f} mm, worst {max(multi_err, default=float('nan')):.2f} mm\n"
            f"pass line: rings fit and two-view median ≤ {PASS_MEDIAN_MM} mm → [bold]{verdict}[/bold]\n"
            f"verdict 1 also needs shafts found automatically in most views: "
            f"{'yes' if shafts['found_in_most_views'] else 'no'}",
            title="verdict input",
            expand=False,
        )
    )
    report_path.write_text(json.dumps({"passed": passed if holes_fit else None, "rings_fit": views_fit,
                                                       "holes_fit": holes_fit,
                                                       "ring_fit_max_rms_mm": RING_FIT_MAX_RMS_MM,
                                                       "median_front_mm": median_single,
                                                       "median_front_visible_mm": median_or_none(single_err[False]),
                                                       "median_front_hidden_mm": median_or_none(single_err[True]),
                                                       "median_two_view_mm": median_multi, "views": views,
                                                       "shafts": shafts,
                                                       "arrows": rows}, indent=2))


if __name__ == "__main__":
    main()
