"""uv run --with opencv-python-headless --with numpy --with pillow --with rich python -m unittest discover -s tools/gate"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cv2

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import click  # noqa: E402
from face import Face, near_line, score  # noqa: E402


class ScoreTest(unittest.TestCase):
    face = Face(400.0)

    def test_shaft_touching_the_line_scores_the_higher_zone(self):
        self.assertEqual(score(self.face, 40.0 + 2.75, 5.5), 9)
        self.assertEqual(score(self.face, 40.0 + 2.76, 5.5), 8)

    def test_centre_and_miss(self):
        self.assertEqual(score(self.face, 0.0, 5.5), 10)
        self.assertEqual(score(self.face, 200.0 + 2.75, 5.5), 1)
        self.assertEqual(score(self.face, 205.0, 5.5), 0)

    def test_arrow_close_to_a_line_is_flagged(self):
        self.assertTrue(near_line(self.face, 41.0 + 2.75, 5.5))
        self.assertFalse(near_line(self.face, 50.0 + 2.75, 5.5))


class FakeEndTest(unittest.TestCase):
    def test_gate_passes_on_a_rendered_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run([sys.executable, str(HERE / "synth.py"), tmp], check=True, capture_output=True)
            subprocess.run([sys.executable, str(HERE / "gate.py"), tmp], check=True, capture_output=True)
            report = json.loads((Path(tmp) / "report.json").read_text())
            truth = json.loads((Path(tmp) / "truth.json").read_text())["entries_face_mm"]
        self.assertTrue(report["rings_fit"])
        self.assertLessEqual(report["median_two_view_mm"], 1.5)
        for row, true in zip(report["arrows"], truth):
            self.assertLess(abs(row["hole_mm"][0] - true[0]) + abs(row["hole_mm"][1] - true[1]), 2.0)


class ClickTest(unittest.TestCase):
    def run_script(self, events, steps, pairs):
        callback = {}
        queue = list(events)

        def wait_key(_):
            while queue:
                kind, value = queue.pop(0)
                if kind == "click":
                    callback["fn"](cv2.EVENT_LBUTTONDOWN, *value, 0, None)
                    return 255
                return ord(value)
            return ord("q")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "p.png"
            cv2.imwrite(str(path), (255 * __import__("numpy").ones((400, 400, 3))).astype("uint8"))
            with mock.patch.multiple(
                click.cv2,
                namedWindow=mock.DEFAULT,
                imshow=mock.DEFAULT,
                setWindowTitle=mock.DEFAULT,
                destroyAllWindows=mock.DEFAULT,
                setMouseCallback=lambda _w, fn: callback.update(fn=fn),
                waitKey=wait_key,
            ):
                return click.collect(path, steps, pairs)

    def test_skip_marks_the_whole_arrow_and_undo_removes_it(self):
        steps = click.prompts(2, holes=False)
        events = [("click", (10, 10)), ("key", "s"), ("key", "u"), ("click", (20, 20)), ("click", (30, 30)),
                  ("key", "s")]
        self.assertEqual(self.run_script(events, steps, True), [[10.0, 10.0], [20.0, 20.0], [30.0, 30.0], None, None])

    def test_skip_is_ignored_on_the_far_point_and_on_holes(self):
        steps = click.prompts(1, holes=False)
        events = [("click", (1, 1)), ("click", (2, 2)), ("key", "s"), ("click", (3, 3))]
        self.assertEqual(self.run_script(events, steps, True), [[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]])
        holes = click.prompts(1, holes=True)
        self.assertEqual(self.run_script([("click", (1, 1)), ("key", "s"), ("click", (5, 5))], holes, False),
                         [[1.0, 1.0], [5.0, 5.0]])

    def test_quit_saves_nothing(self):
        self.assertIsNone(self.run_script([("key", "q")], click.prompts(1, holes=True), False))


if __name__ == "__main__":
    unittest.main()
