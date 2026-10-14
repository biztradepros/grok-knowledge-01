"""시험 공용 도구. 시험마다 새 임시 폴더를 루트로 쓴다."""

import atexit
import copy
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(ENGINE / "fixtures"))

import make_fixture  # noqa: E402
from df_compose import compose  # noqa: E402
from df_compose.contract import Limits  # noqa: E402

FONT = ENGINE / "assets" / "fonts" / "NanumGothic-Regular.ttf"
FONT_LICENSE = ENGINE / "assets" / "fonts" / "OFL.txt"
FONT_SHA = json.loads((ENGINE / "assets" / "fonts" / "fonts.json").read_text())["fonts"][0]["sha256"]
SRT = ENGINE / "fixtures" / "subtitles_ko.srt"
CUES = json.loads((ENGINE / "fixtures" / "subtitles_ko.json").read_text(encoding="utf-8"))
ENV = "TEST"

_FIXTURE_CACHE = {}


def fixture_video():
    """결정론적 입력 영상. 프로세스당 한 번만 만든다."""
    if "path" not in _FIXTURE_CACHE:
        d = Path(tempfile.mkdtemp(prefix="dfc-fixture-"))
        path = d / "fixture.mp4"
        _FIXTURE_CACHE["sha"] = make_fixture.make(str(path))
        _FIXTURE_CACHE["path"] = path
        atexit.register(shutil.rmtree, d, True)
    return _FIXTURE_CACHE["path"]


def ffmpeg(*args, timeout=120):
    subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-y", *args], check=True, timeout=timeout)


class EngineCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dfc-test-"))
        self.root = self.tmp / "in"
        self.root.mkdir()
        self.out = self.tmp / "out"
        self.video = self.root / "input.mp4"
        shutil.copyfile(fixture_video(), self.video)
        self.roots = [str(self.root), str(ENGINE / "assets"), str(ENGINE / "fixtures")]

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def request(self, **over):
        req = {
            "contract": "df.compose.v1",
            "job_id": "DF-JOB-TEST-001",
            "video_uri": self.video.as_uri(),
            "subtitles_json_or_srt": copy.deepcopy(CUES),
            "output_size": [540, 960],
            "output_fps": 30,
            "safe_area": {"top": 0.1, "bottom": 0.18, "left": 0.06, "right": 0.06},
            "font_asset": {"uri": FONT.as_uri(), "sha256": FONT_SHA, "license": "OFL-1.1",
                           "license_uri": FONT_LICENSE.as_uri()},
        }
        req.update(over)
        return req

    def run_job(self, req=None, limits=Limits(), **over):
        return compose(req if req is not None else self.request(**over), self.roots, self.out, ENV, limits)

    def assertFailed(self, result, code):
        self.assertEqual(result["state"], "FAILED", result.get("output"))
        self.assertEqual(result["error"]["code"], code, json.dumps(result["error"], ensure_ascii=False)[:800])
        self.assertNoLeftovers()

    def assertNoLeftovers(self):
        if self.out.exists():
            hidden = [p.name for p in self.out.iterdir() if p.name.startswith(".")]
            self.assertEqual(hidden, [], "임시 작업 폴더가 남았습니다")
