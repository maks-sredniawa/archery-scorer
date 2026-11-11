#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["opencv-python>=4.10", "numpy>=1.26", "rich>=13"]
# ///
"""Click the points gate.py needs on real photos, and write clicks.json beside them.

    uv run --script tools/gate/click.py RUN_DIR --views front.jpg left.jpg right.jpg --holes holes.jpg

In every photo, click the reference point first (the same physical spot each time, such as the face
paper's top-left corner). Then, arrow by arrow in the same order every time:

  views:  where the shaft meets the face (or the lowest point of it you can see), then a point far
          up the shaft, before the fletching
  holes:  the centre of each hole

Keys: s = this arrow is not visible in this photo (views only, at its first point), u = undo, q = quit without saving.
A magnifier follows the mouse in the top-left corner.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from rich.console import Console

console = Console()
ZOOM, LENS = 4, 90


def prompts(arrows: int, holes: bool) -> list[str]:
    steps = ["reference point"]
    for i in range(1, arrows + 1):
        steps += [f"hole {i}"] if holes else [f"arrow {i}: where it meets the face", f"arrow {i}: far up the shaft"]
    return steps


def collect(path: Path, steps: list[str], pairs: bool) -> list | None:
    image = cv2.imread(str(path))
    if image is None:
        raise SystemExit(f"cannot read {path}")
    points: list = []
    mouse = [0, 0]

    def on_mouse(event, x, y, *_):
        mouse[:] = [x, y]
        if event == cv2.EVENT_LBUTTONDOWN and len(points) < len(steps):
            points.append([float(x), float(y)])

    cv2.namedWindow("click", cv2.WINDOW_NORMAL)
    cv2.setMouseCallback("click", on_mouse)
    while len(points) < len(steps):
        frame = image.copy()
        for p in points:
            if p is not None:
                cv2.drawMarker(frame, (int(p[0]), int(p[1])), (255, 0, 255), cv2.MARKER_CROSS, 30, 2)
        x, y = mouse
        h, w = image.shape[:2]
        x0, y0 = max(min(x - LENS, w - 2 * LENS), 0), max(min(y - LENS, h - 2 * LENS), 0)
        lens = cv2.resize(image[y0 : y0 + 2 * LENS, x0 : x0 + 2 * LENS], None, fx=ZOOM, fy=ZOOM, interpolation=cv2.INTER_NEAREST)
        cv2.drawMarker(lens, ((x - x0) * ZOOM, (y - y0) * ZOOM), (255, 0, 255), cv2.MARKER_CROSS, 40, 1)
        lens = lens[: h // 2, : w // 2]
        frame[: lens.shape[0], : lens.shape[1]] = lens
        cv2.setWindowTitle("click", f"{path.name}: {steps[len(points)]}   (s skip, u undo, q quit)")
        cv2.imshow("click", frame)
        key = cv2.waitKey(30) & 0xFF
        if key == ord("q"):
            cv2.destroyAllWindows()
            return None
        if key == ord("u") and points:
            if points.pop() is None:
                points.pop()
        if key == ord("s") and pairs and len(points) % 2 == 1:
            points += [None, None]
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run", type=Path)
    parser.add_argument("--views", nargs="+", required=True)
    parser.add_argument("--holes", required=True)
    parser.add_argument("--arrows", type=int, default=6)
    parser.add_argument("--face-cm", type=float, default=40)
    parser.add_argument("--shaft-mm", type=float, required=True, help="the arrow shaft's outside diameter")
    parser.add_argument("--line-mm", type=float, default=1.0, help="the face's dividing-line width")
    args = parser.parse_args()

    clicks = {"face_mm": args.face_cm * 10, "line_mm": args.line_mm, "shaft_mm": args.shaft_mm, "views": []}
    view_steps = prompts(args.arrows, holes=False)
    for i, name in enumerate(args.views, 1):
        console.print(f"[{i}/{len(args.views) + 1}] {name} ...")
        pts = collect(args.run / name, view_steps, pairs=True)
        if pts is None:
            raise SystemExit("quit, nothing saved")
        arrows = [None if pts[j] is None else {"near": pts[j], "far": pts[j + 1]} for j in range(1, len(pts), 2)]
        clicks["views"].append({"image": name, "ref": pts[0], "arrows": arrows})

    console.print(f"[{len(args.views) + 1}/{len(args.views) + 1}] {args.holes} ...")
    pts = collect(args.run / args.holes, prompts(args.arrows, holes=True), pairs=False)
    if pts is None:
        raise SystemExit("quit, nothing saved")
    clicks["holes"] = {"image": args.holes, "ref": pts[0], "arrows": pts[1:]}
    cv2.destroyAllWindows()
    (args.run / "clicks.json").write_text(json.dumps(clicks, indent=2))
    console.print(f"wrote {args.run / 'clicks.json'}; next: uv run --script tools/gate/gate.py {args.run}")


if __name__ == "__main__":
    main()
