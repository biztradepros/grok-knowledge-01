"""자막이 정해진 프레임에서만 보이는지. 경계 앞뒤 프레임을 직접 꺼내 확인한다."""

import unittest

from support import EngineCase, ffmpeg

from df_compose import render


class TimingTests(EngineCase):
    def grab(self, mp4, frame_no, fps, name, source=False):
        out = self.tmp / name
        t = max(0.0, (frame_no - 0.2) / fps)
        vf = ["-vf", "scale=w=540:h=960:force_original_aspect_ratio=increase,crop=540:960"] if source else []
        ffmpeg("-ss", f"{t:.4f}", "-i", str(mp4), "-frames:v", "1", *vf, "-update", "1", str(out))
        return out

    def test_visible_only_inside_window(self):
        kept = {}
        original = render._overlay_match

        def spy(frame, base, ov):
            kept.setdefault("ov", dict(ov, path=self.tmp / "cue.png"))
            (self.tmp / "cue.png").write_bytes(ov["path"].read_bytes())
            return original(frame, base, ov)

        render._overlay_match = spy
        try:
            r = self.run_job(output_fps=30, subtitles_json_or_srt=[{"start": 1.0, "end": 2.0, "text": "타이밍 시험"}])
        finally:
            render._overlay_match = original
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        mp4 = self.out / "DF-JOB-TEST-001" / "output.mp4"
        ov = kept["ov"]
        # 30fps: 29번 = 0.967초(전), 31번 = 1.033초(안), 59번 = 1.967초(안), 61번 = 2.033초(후)
        expect = {29: False, 31: True, 45: True, 59: True, 61: False}
        for n, visible in expect.items():
            frame = self.grab(mp4, n, 30, f"o{n}.png")
            base = self.grab(self.video, n, 30, f"b{n}.png", source=True)
            self.assertEqual(render._overlay_match(frame, base, ov)["ok"], visible, f"frame {n}")

    def test_cue_shorter_than_frame(self):
        r = self.run_job(output_fps=24, subtitles_json_or_srt=[{"start": 1.0, "end": 1.03, "text": "짧음"}])
        self.assertFailed(r, "CUE_SHORTER_THAN_FRAME")

    def test_200_cues_single_track_input(self):
        cues = [{"start": round(i * 0.03, 3), "end": round(i * 0.03 + 0.025, 3), "text": f"자막 {i:03d}"}
                for i in range(200)]
        r = self.run_job(output_fps=60, subtitles_json_or_srt=cues)
        self.assertEqual(r["state"], "ASSET_READY", r.get("error"))
        self.assertEqual(r["subtitles"]["count"], 200)
        self.assertEqual(r["render"]["argv"].count("-i"), 2)  # 원본 + 자막 트랙. 자막 수와 무관.


if __name__ == "__main__":
    unittest.main()
