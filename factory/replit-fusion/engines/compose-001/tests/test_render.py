import json
import unittest

from support import ENGINE, EngineCase, ffmpeg

from df_compose.contract import Limits


class RenderTests(EngineCase):
    def test_end_to_end(self):
        r = self.run_job()
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        self.assertTrue(all(r["checks"].values()), r["checks"])
        job = self.out / "DF-JOB-TEST-001"
        self.assertEqual(sorted(p.name for p in job.iterdir()), ["output.ffprobe.json", "output.mp4", "result.json"])
        saved = json.loads((job / "result.json").read_text())
        self.assertEqual(saved["output"]["sha256"], r["output"]["sha256"])
        self.assertEqual(saved["input"]["sha256"], r["input"]["sha256"])
        self.assertEqual(r["environment"]["label"], "TEST")
        self.assertEqual(r["subtitles"]["count"], 3)
        self.assertNoLeftovers()

    def test_deterministic_and_srt_equals_json(self):
        a = self.run_job(job_id="DF-JOB-DET-A")
        b = self.run_job(job_id="DF-JOB-DET-B",
                         subtitles_json_or_srt={"format": "srt", "uri": (ENGINE / "fixtures" / "subtitles_ko.srt").as_uri()})
        self.assertEqual(a["state"], "ASSET_READY", a.get("error"))
        self.assertEqual(b["state"], "ASSET_READY", b.get("error"))
        self.assertEqual(a["subtitles"]["sha256"], b["subtitles"]["sha256"])
        self.assertEqual(a["output"]["sha256"], b["output"]["sha256"])

    def test_input_without_audio_gets_silent_aac(self):
        silent = self.root / "silent.mp4"
        ffmpeg("-i", str(self.video), "-an", "-c:v", "copy", str(silent))
        r = self.run_job(video_uri=silent.as_uri())
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        self.assertFalse(r["input"]["has_audio"])
        self.assertTrue(r["checks"]["audio_aac"])

    def test_landscape_to_square_and_webm_input(self):
        webm = self.root / "in.webm"
        ffmpeg("-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=2", "-c:v", "libvpx-vp9",
               "-deadline", "realtime", str(webm))
        r = self.run_job(video_uri=webm.as_uri(), output_size=[720, 720], output_fps=24,
                         subtitles_json_or_srt=[{"start": 0.2, "end": 1.8, "text": "정사각형 시험"}])
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        self.assertEqual(r["input"]["demuxer"], "matroska")

    def test_job_exists_is_not_overwritten(self):
        first = self.run_job()
        self.assertEqual(first["state"], "ASSET_READY", first.get("error"))
        before = (self.out / "DF-JOB-TEST-001" / "output.mp4").read_bytes()
        second = self.run_job(subtitles_json_or_srt=[{"start": 0, "end": 1, "text": "다른 자막"}])
        self.assertFailed(second, "JOB_EXISTS")
        self.assertEqual((self.out / "DF-JOB-TEST-001" / "output.mp4").read_bytes(), before)

    def test_timeout_rolls_back(self):
        r = self.run_job(limits=Limits(timeout_seconds=0.05))
        self.assertFailed(r, "TIMEOUT")
        self.assertFalse((self.out / "DF-JOB-TEST-001").exists())
        failed = list((self.out / "_failed").glob("DF-JOB-TEST-001.*.json"))
        self.assertEqual(len(failed), 1)
        self.assertIn("stderr", json.loads(failed[0].read_text())["error"]["detail"])

    def test_missing_glyph(self):
        r = self.run_job(subtitles_json_or_srt=[{"start": 0, "end": 1, "text": "웃음 😀"}])
        self.assertFailed(r, "GLYPH_MISSING")
        self.assertIn("😀", r["error"]["detail"]["chars"])

    def test_cue_too_long_for_area(self):
        long_text = " ".join(["가나다라마바사아자차카타파하"] * 12)
        r = self.run_job(subtitles_json_or_srt=[{"start": 0, "end": 1, "text": long_text}])
        self.assertFailed(r, "CUE_TOO_LONG_FOR_AREA")

    def test_result_never_raises(self):
        r = self.run_job(req=["not", "a", "dict"])
        self.assertFailed(r, "BAD_REQUEST")


if __name__ == "__main__":
    unittest.main()
