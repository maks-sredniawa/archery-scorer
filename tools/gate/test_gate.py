"""uv run -q --with opencv-python-headless --with numpy --with pillow --with rich python -m unittest discover -s tools/gate"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import cv2
import numpy as np

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
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.run_dir = Path(cls.tmp.name)
        subprocess.run([sys.executable, str(HERE / "synth.py"), cls.tmp.name], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def gate(self) -> dict:
        subprocess.run([sys.executable, str(HERE / "gate.py"), str(self.run_dir)], check=True, capture_output=True)
        return json.loads((self.run_dir / "report.json").read_text())

    def test_gate_passes_on_a_rendered_end(self):
        report = self.gate()
        truth = json.loads((self.run_dir / "truth.json").read_text())["entries_face_mm"]
        self.assertTrue(report["rings_fit"])
        self.assertTrue(report["holes_fit"])
        self.assertTrue(report["passed"])
        self.assertLessEqual(report["median_two_view_mm"], 1.5)
        for row, true in zip(report["arrows"], truth):
            self.assertLess(abs(row["hole_mm"][0] - true[0]) + abs(row["hole_mm"][1] - true[1]), 2.0)

    def test_hidden_entries_are_counted_per_view_and_split_from_visible_ones(self):
        clicks_path = self.run_dir / "clicks.json"
        original = clicks_path.read_text()
        clicks = json.loads(original)
        for arrow in clicks["views"][0]["arrows"][:2]:
            arrow["near_hidden"] = True
        clicks["views"][1]["arrows"][0]["near_hidden"] = True
        clicks_path.write_text(json.dumps(clicks))
        try:
            report = self.gate()
        finally:
            clicks_path.write_text(original)
        self.assertEqual([v["entry_hidden"] for v in report["views"]], [2, 1, 0])
        self.assertEqual([row["front_entry_hidden"] for row in report["arrows"]], [True, True] + [False] * 4)
        errors = [row["front_only_mm"] for row in report["arrows"]]
        self.assertAlmostEqual(report["median_front_hidden_mm"], float(np.median(errors[:2])))
        self.assertAlmostEqual(report["median_front_visible_mm"], float(np.median(errors[2:])))

    def test_a_holes_photo_without_rings_is_no_reading_not_a_stale_pass(self):
        self.gate()
        holes = self.run_dir / "holes.jpg"
        original = holes.read_bytes()
        cv2.imwrite(str(holes), np.full((900, 1200, 3), 200, np.uint8))
        try:
            result = subprocess.run([sys.executable, str(HERE / "gate.py"), str(self.run_dir)], capture_output=True)
        finally:
            holes.write_bytes(original)
        self.assertEqual(result.returncode, 1)
        report = json.loads((self.run_dir / "report.json").read_text())
        self.assertIsNone(report["passed"])
        self.assertFalse(report["holes_fit"])

    def test_views_without_rings_fail_rather_than_give_no_reading(self):
        self.gate()
        clicks = json.loads((self.run_dir / "clicks.json").read_text())
        paths = [self.run_dir / view["image"] for view in clicks["views"]]
        originals = [path.read_bytes() for path in paths]
        for path in paths:
            cv2.imwrite(str(path), np.full((900, 1200, 3), 200, np.uint8))
        try:
            result = subprocess.run([sys.executable, str(HERE / "gate.py"), str(self.run_dir)], capture_output=True)
        finally:
            for path, original in zip(paths, originals):
                path.write_bytes(original)
        self.assertEqual(result.returncode, 1)
        report = json.loads((self.run_dir / "report.json").read_text())
        self.assertIs(report["passed"], False)
        self.assertFalse(report["rings_fit"])
        self.assertTrue(report["holes_fit"])

    def test_a_holes_photo_whose_rings_miss_is_no_reading_even_when_no_view_has_rings(self):
        self.gate()
        clicks = json.loads((self.run_dir / "clicks.json").read_text())
        views = [self.run_dir / view["image"] for view in clicks["views"]]
        holes = self.run_dir / clicks["holes"]["image"]
        originals = {path: path.read_bytes() for path in [*views, holes]}
        for path in views:
            cv2.imwrite(str(path), np.full((900, 1200, 3), 200, np.uint8))
        image = cv2.imread(str(holes))
        width, height = image.shape[1], image.shape[0]
        stretch = np.float32([[1.2, 0, -0.1 * width], [0, 1, 0]])
        cv2.imwrite(str(holes), cv2.warpAffine(image, stretch, (width, height), borderValue=(200, 170, 115)))
        try:
            result = subprocess.run([sys.executable, str(HERE / "gate.py"), str(self.run_dir)], capture_output=True)
        finally:
            for path, original in originals.items():
                path.write_bytes(original)
        self.assertEqual(result.returncode, 1)
        report = json.loads((self.run_dir / "report.json").read_text())
        self.assertIsNone(report["passed"])
        self.assertFalse(report["holes_fit"])
        self.assertEqual(report["reason"], "NO READING: retake the holes photo")

    def test_a_folder_without_clicks_says_so(self):
        with tempfile.TemporaryDirectory() as empty:
            result = subprocess.run([sys.executable, str(HERE / "gate.py"), empty], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("run click.py", result.stderr)
        self.assertNotIn("Traceback", result.stderr)


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
            cv2.imwrite(str(path), np.full((400, 400, 3), 255, np.uint8))
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
        self.assertEqual(self.run_script(events, steps, True),
                         ([[10.0, 10.0], [20.0, 20.0], [30.0, 30.0], None, None], set()))

    def test_skip_is_ignored_on_the_far_point_and_on_holes(self):
        steps = click.prompts(1, holes=False)
        events = [("click", (1, 1)), ("click", (2, 2)), ("key", "s"), ("click", (3, 3))]
        self.assertEqual(self.run_script(events, steps, True), ([[1.0, 1.0], [2.0, 2.0], [3.0, 3.0]], set()))
        holes = click.prompts(1, holes=True)
        self.assertEqual(self.run_script([("click", (1, 1)), ("key", "s"), ("click", (5, 5))], holes, False),
                         ([[1.0, 1.0], [5.0, 5.0]], set()))

    def test_hidden_marks_the_near_point_just_clicked(self):
        steps = click.prompts(2, holes=False)
        events = [("click", (1, 1)), ("click", (2, 2)), ("key", "h"), ("click", (3, 3)),
                  ("click", (4, 4)), ("click", (5, 5))]
        points, hidden = self.run_script(events, steps, True)
        self.assertEqual(hidden, {1})
        self.assertEqual(len(points), 5)

    def test_hidden_is_ignored_off_the_near_point_on_skipped_arrows_and_on_holes(self):
        steps = click.prompts(2, holes=False)
        events = [("key", "h"), ("click", (1, 1)), ("key", "h"), ("key", "s"), ("key", "h"),
                  ("click", (4, 4)), ("click", (5, 5))]
        self.assertEqual(self.run_script(events, steps, True)[1], set())
        holes = click.prompts(2, holes=True)
        events = [("click", (1, 1)), ("click", (2, 2)), ("key", "h"), ("click", (3, 3))]
        self.assertEqual(self.run_script(events, holes, False)[1], set())

    def test_undo_clears_the_hidden_mark(self):
        steps = click.prompts(1, holes=False)
        events = [("click", (1, 1)), ("click", (2, 2)), ("key", "h"), ("key", "u"), ("click", (2, 2)),
                  ("click", (3, 3))]
        self.assertEqual(self.run_script(events, steps, True)[1], set())

    def test_magnifier_sits_in_the_corner_farthest_from_the_mouse(self):
        size, lens = (1000, 800), (300, 200)
        self.assertEqual(click.lens_corner((10, 10), size, lens), (700, 600))
        self.assertEqual(click.lens_corner((990, 10), size, lens), (0, 600))
        self.assertEqual(click.lens_corner((10, 790), size, lens), (700, 0))
        self.assertEqual(click.lens_corner((990, 790), size, lens), (0, 0))

    def test_quit_saves_nothing(self):
        self.assertIsNone(self.run_script([("key", "q")], click.prompts(1, holes=True), False))


if __name__ == "__main__":
    unittest.main()
