"""자막 표시 검사가 형식적 통과가 아님을 보이는 음성 대조."""

import shutil
import tempfile
import unittest
from pathlib import Path

import support  # noqa: F401  (sys.path 설정)

from PIL import Image, ImageDraw

from df_compose.render import _overlay_match


class OverlayCheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dfc-ov-"))
        cue = Image.new("RGBA", (200, 60), (0, 0, 0, 0))
        ImageDraw.Draw(cue).rectangle((20, 10, 180, 50), fill=(255, 255, 255, 255), outline=(0, 0, 0, 255), width=4)
        self.cue_path = self.tmp / "cue.png"
        cue.save(self.cue_path)
        base = Image.new("RGB", (300, 200), (40, 90, 200))
        self.base_path = self.tmp / "base.png"
        base.save(self.base_path)
        composed = base.copy()
        composed.paste(cue, (50, 100), cue)
        self.composed_path = self.tmp / "composed.png"
        composed.save(self.composed_path)
        self.ov = {"index": 0, "path": self.cue_path, "x": 50, "y": 100, "w": 200, "h": 60}

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_drawn_subtitle_passes(self):
        self.assertTrue(_overlay_match(self.composed_path, self.base_path, self.ov)["ok"])

    def test_missing_subtitle_fails(self):
        r = _overlay_match(self.base_path, self.base_path, self.ov)
        self.assertFalse(r["ok"], r)
        self.assertEqual(r["closer_to_subtitle_ratio"], 0.0)

    def test_wrong_position_fails(self):
        moved = Image.open(self.base_path).copy()
        cue = Image.open(self.cue_path)
        moved.paste(cue, (50, 20), cue)
        moved_path = self.tmp / "moved.png"
        moved.save(moved_path)
        self.assertFalse(_overlay_match(moved_path, self.base_path, self.ov)["ok"])


if __name__ == "__main__":
    unittest.main()
