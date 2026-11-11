#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["opencv-python-headless>=4.10", "numpy>=1.26", "pillow>=10", "rich>=13"]
# ///
"""Phase 0's gate (docs/phase-0.md, section 1): score one photographed end against the holes it left.

    uv run --script tools/gate/gate.py RUN_DIR

RUN_DIR holds the photos and clicks.json, written by click.py (or synth.py for a fake end). Prints
readings R1 to R3 and writes report.json beside them.
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
from face import Face, fit_rings, near_line, score, single_view_entry, triangulated_entry  # noqa: E402

PASS_MEDIAN_MM = 1.5
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


def load_plane(run: Path, entry: dict, face: Face, label: str):
    path = run / entry["image"]
    image = cv2.imread(str(path))
    if image is None:
        raise SystemExit(f"cannot read {path}")
    with console.status(f"fitting rings in {label} ..."):
        fit = fit_rings(image, focal_px(path, entry), face, entry["ref"])
    return fit


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    args = parser.parse_args()
    clicks = json.loads((args.run / "clicks.json").read_text())
    face = Face(clicks.get("face_mm", 400.0), clicks.get("line_mm", 1.0))
    shaft = float(clicks["shaft_mm"])
    console.print(Panel(f"Phase 0 gate · {args.run} · {face.diameter_mm / 10:.0f} cm face · shaft {shaft} mm", expand=False))

    rings = Table(title="R1 · ring fit per photo (RMS distance from the nominal edge, mm)")
    for col in ("photo", "gold", "red", "blue", "fits"):
        rings.add_column(col)
    planes, all_fit = [], True
    labelled = [(v["image"], v) for v in clicks["views"]] + [(clicks["holes"]["image"] + " (holes)", clicks["holes"])]
    for label, entry in labelled:
        fit = load_plane(args.run, entry, face, label)
        ok = fit.plane is not None and max(fit.residual_mm["red"], fit.residual_mm["blue"]) < 1.0
        all_fit &= ok
        cells = [f"{fit.residual_mm[n]:.2f}" for n in ("gold", "red", "blue")] if fit.plane else ["-"] * 3
        rings.add_row(label, *cells, "yes" if ok else f"no {fit.reason}".strip())
        planes.append(fit.plane)
    console.print(rings)
    view_planes, holes_plane = planes[:-1], planes[-1]
    if holes_plane is None or not any(view_planes):
        console.print("[red]Rings did not fit where they had to; no entry point can be computed.[/red]")
        raise SystemExit(1)

    holes = [holes_plane.to_face(p) for p in clicks["holes"]["arrows"]]
    table = Table(title="R2/R3 · entry point against the hole, mm")
    for col in ("arrow", "hole", "seen in", "front only", "two views", "angle", "score: hole / two views", "check"):
        table.add_column(col)
    single_err, multi_err, rows = [], [], []
    for i, hole in enumerate(holes):
        seen = [
            (plane, view["arrows"][i]["near"], view["arrows"][i]["far"])
            for plane, view in zip(view_planes, clicks["views"])
            if plane is not None and view["arrows"][i] is not None
        ]
        front = clicks["views"][0]["arrows"][i]
        single = single_view_entry(view_planes[0], front["near"]) if view_planes[0] and front else None
        multi, angle = triangulated_entry(seen) if len(seen) >= 2 else (None, 0.0)
        s_err = float(np.linalg.norm(single - hole)) if single is not None else None
        m_err = float(np.linalg.norm(multi - hole)) if multi is not None else None
        if s_err is not None:
            single_err.append(s_err)
        if m_err is not None:
            multi_err.append(m_err)
        hole_r = float(np.linalg.norm(hole))
        est_score = score(face, float(np.linalg.norm(multi)), shaft) if multi is not None else None
        flag = "near a line" if near_line(face, hole_r, shaft) else ""
        table.add_row(
            str(i + 1),
            f"({hole[0]:.1f}, {hole[1]:.1f})",
            str(len(seen)),
            f"{s_err:.2f}" if s_err is not None else "-",
            f"{m_err:.2f}" if m_err is not None else "-",
            f"{angle:.0f}°",
            f"{score(face, hole_r, shaft)} / {est_score if est_score is not None else '-'}",
            flag,
        )
        rows.append({"arrow": i + 1, "hole_mm": hole.tolist(), "views": len(seen), "front_only_mm": s_err,
                     "two_view_mm": m_err, "angle_deg": angle, "hole_score": score(face, hole_r, shaft),
                     "two_view_score": est_score})
    console.print(table)

    median_multi = statistics.median(multi_err) if multi_err else float("inf")
    median_single = statistics.median(single_err) if single_err else float("inf")
    passed = all_fit and median_multi <= PASS_MEDIAN_MM
    console.print(
        Panel(
            f"rings fit in every photo: {'yes' if all_fit else 'no'}\n"
            f"front photo only: median {median_single:.2f} mm, worst {max(single_err, default=float('nan')):.2f} mm\n"
            f"two or more views: median {median_multi:.2f} mm, worst {max(multi_err, default=float('nan')):.2f} mm\n"
            f"pass line: rings fit and two-view median ≤ {PASS_MEDIAN_MM} mm → [bold]{'PASS' if passed else 'FAIL'}[/bold]",
            title="verdict input",
            expand=False,
        )
    )
    (args.run / "report.json").write_text(json.dumps({"passed": passed, "rings_fit": all_fit,
                                                       "median_front_mm": median_single,
                                                       "median_two_view_mm": median_multi, "arrows": rows}, indent=2))


if __name__ == "__main__":
    main()
