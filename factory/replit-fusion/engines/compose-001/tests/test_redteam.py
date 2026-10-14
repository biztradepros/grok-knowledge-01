"""레드팀 시험. REDTEAM.md 의 항목 번호와 맞춘다."""

import json
import os
import shutil
import unittest

from support import EngineCase, ffmpeg

from df_compose.contract import Limits


class InjectionTests(EngineCase):
    def test_rt01_subtitle_text_is_never_in_argv(self):
        evil = "'; drawtext=text=pwned [x]; movie=/etc/passwd -y /tmp/x $(touch pwned)"
        r = self.run_job(output_size=[1080, 1920], style={"font_size_ratio": 0.025},
                         subtitles_json_or_srt=[{"start": 0.5, "end": 2.0, "text": evil}])
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        argv = json.dumps(r["render"]["argv"], ensure_ascii=False)
        self.assertNotIn("pwned", argv)
        self.assertNotIn("passwd", argv)
        self.assertFalse(os.path.exists("pwned"))

    def test_rt02_hostile_filename(self):
        name = self.root / "-i evil;$(touch pwned)|x'.mp4"
        shutil.copyfile(self.video, name)
        r = self.run_job(video_uri=str(name))
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        self.assertIn("file:" + str(name), r["render"]["argv"])
        self.assertFalse(os.path.exists("pwned"))
        self.assertFalse((self.root / "pwned").exists())


class MaliciousMediaTests(EngineCase):
    def test_rt03_hls_playlist_disguised_as_mp4(self):
        fake = self.root / "playlist.mp4"
        fake.write_text("#EXTM3U\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:1.0,\nfile:///etc/passwd\n#EXT-X-ENDLIST\n")
        r = self.run_job(video_uri=str(fake))
        self.assertFailed(r, "CONTAINER_NOT_ALLOWED")
        self.assertEqual(r["error"]["stage"], "probe_input")
        self.assertNotIn("render", r)

    def test_rt04_concat_script_disguised(self):
        fake = self.root / "concat.mkv"
        fake.write_text("ffconcat version 1.0\nfile '/etc/passwd'\n")
        self.assertFailed(self.run_job(video_uri=str(fake)), "CONTAINER_NOT_ALLOWED")

    def test_rt05_text_and_image_disguised(self):
        txt = self.root / "a.mp4"
        txt.write_text("hello")
        self.assertFailed(self.run_job(video_uri=str(txt)), "CONTAINER_NOT_ALLOWED")
        png = self.root / "b.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=c=red:s=64x64:d=1", "-frames:v", "1", "-f", "image2", str(png))
        self.assertFailed(self.run_job(video_uri=str(png)), "CONTAINER_NOT_ALLOWED")

    def test_rt06_truncated_mp4(self):
        cut = self.root / "cut.mp4"
        data = self.video.read_bytes()
        cut.write_bytes(data[: len(data) // 3])
        r = self.run_job(video_uri=str(cut))
        self.assertEqual(r["state"], "FAILED")
        self.assertIn(r["error"]["stage"], ("probe_input", "render", "verify"))
        self.assertNoLeftovers()
        self.assertFalse((self.out / "DF-JOB-TEST-001").exists())

    def test_rt07_audio_only_mp4(self):
        audio = self.root / "audio.mp4"
        ffmpeg("-f", "lavfi", "-i", "sine=duration=1", "-c:a", "aac", "-f", "mp4", str(audio))
        self.assertFailed(self.run_job(video_uri=str(audio)), "NO_VIDEO_STREAM")


class ResourceTests(EngineCase):
    def test_rt08_dimension_limit(self):
        big = self.root / "big.mp4"
        ffmpeg("-f", "lavfi", "-i", "color=c=black:s=4200x4200:d=0.2", "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", str(big))
        self.assertFailed(self.run_job(video_uri=str(big)), "BAD_DIMENSIONS")

    def test_rt09_duration_limit(self):
        self.assertFailed(self.run_job(limits=Limits(max_input_seconds=3)), "BAD_DURATION")

    def test_rt10_input_size_limit(self):
        self.assertFailed(self.run_job(limits=Limits(max_input_bytes=1000)), "FILE_TOO_LARGE")

    def test_rt11_output_size_limit(self):
        r = self.run_job(limits=Limits(max_output_bytes=50_000))
        self.assertFailed(r, "OUTPUT_SIZE_LIMIT")

    def test_rt12_memory_limit(self):
        r = self.run_job(limits=Limits(max_memory_bytes=48 * 1024 * 1024))
        self.assertEqual(r["state"], "FAILED")
        self.assertIn(r["error"]["stage"], ("probe_input", "render"))
        self.assertNoLeftovers()


if __name__ == "__main__":
    unittest.main()
