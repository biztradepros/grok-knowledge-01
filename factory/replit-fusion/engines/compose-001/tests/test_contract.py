import os
import unittest

from support import ENGINE, FONT, EngineCase

from df_compose.contract import Limits, parse_request
from df_compose.errors import ComposeError
from df_compose.subtitles import clean_text, load_cues, parse_srt


class ContractTests(EngineCase):
    def code(self, req):
        with self.assertRaises(ComposeError) as ctx:
            parse_request(req, self.roots)
        return ctx.exception.code

    def test_valid_request(self):
        req = parse_request(self.request(), self.roots)
        self.assertEqual(req.output_size, (540, 960))
        self.assertEqual(len(req.canonical_sha256()), 64)

    def test_bad_job_ids(self):
        for job in ["../x", "a", "a/b", "-rf", "x" * 200, "ab..cd", "잡", 7, None]:
            self.assertEqual(self.code(self.request(job_id=job)), "BAD_JOB_ID", job)

    def test_remote_schemes_rejected(self):
        for uri in ["https://example.com/a.mp4", "http://169.254.169.254/x", "ftp://h/a.mp4",
                    "concat:a.mp4|b.mp4", "data:video/mp4;base64,AAAA", "file://evil.host/etc/passwd"]:
            self.assertEqual(self.code(self.request(video_uri=uri)), "SCHEME_NOT_ALLOWED", uri)

    def test_path_outside_roots(self):
        self.assertEqual(self.code(self.request(video_uri="/etc/passwd")), "PATH_OUTSIDE_ROOTS")
        self.assertEqual(self.code(self.request(video_uri=str(self.root / ".." / ".." / "etc" / "passwd"))),
                         "PATH_OUTSIDE_ROOTS")

    def test_symlink_escape(self):
        link = self.root / "link.mp4"
        os.symlink("/etc/hostname", link)
        self.assertEqual(self.code(self.request(video_uri=str(link))), "PATH_OUTSIDE_ROOTS")

    def test_not_regular_file(self):
        fifo = self.root / "pipe.mp4"
        os.mkfifo(fifo)
        self.assertEqual(self.code(self.request(video_uri=str(fifo))), "NOT_REGULAR_FILE")
        self.assertEqual(self.code(self.request(video_uri=str(self.root))), "NOT_REGULAR_FILE")

    def test_nul_byte(self):
        self.assertEqual(self.code(self.request(video_uri=str(self.video) + "\x00.txt")), "BAD_URI")

    def test_font_checks(self):
        req = self.request()
        req["font_asset"]["sha256"] = "0" * 64
        self.assertEqual(self.code(req), "FONT_HASH_MISMATCH")
        req = self.request()
        req["font_asset"]["license"] = "Proprietary"
        self.assertEqual(self.code(req), "FONT_LICENSE_NOT_ALLOWED")
        req = self.request()
        req["font_asset"]["uri"] = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        self.assertEqual(self.code(req), "PATH_OUTSIDE_ROOTS")

    def test_numbers(self):
        self.assertEqual(self.code(self.request(output_size=[541, 960])), "BAD_FIELD")
        self.assertEqual(self.code(self.request(output_size=[99999, 960])), "BAD_FIELD")
        self.assertEqual(self.code(self.request(output_fps=float("nan"))), "BAD_FIELD")
        self.assertEqual(self.code(self.request(output_fps=True)), "BAD_FIELD")
        self.assertEqual(self.code(self.request(output_fps=29.97)), "BAD_FIELD")
        self.assertEqual(self.code(self.request(safe_area={"top": 0.9, "bottom": 0, "left": 0, "right": 0})),
                         "BAD_FIELD")

    def test_unknown_field_and_style_injection(self):
        self.assertEqual(self.code(self.request(extra_ffmpeg_args=["-i", "x"])), "UNKNOWN_FIELD")
        self.assertEqual(self.code(self.request(style={"fill": "white:drawtext=text=x"})), "BAD_FIELD")
        self.assertEqual(self.code(self.request(style={"vf": "x"})), "BAD_FIELD")


class SubtitleTests(EngineCase):
    def test_srt_and_json_same_cues(self):
        srt = (ENGINE / "fixtures" / "subtitles_ko.srt").read_text(encoding="utf-8")
        a = load_cues({"format": "srt", "text": srt}, self.roots, Limits(), 6.0)
        b = load_cues(self.request()["subtitles_json_or_srt"], self.roots, Limits(), 6.0)
        self.assertEqual(a[1], b[1])

    def test_srt_bom_crlf(self):
        cues = parse_srt("﻿1\r\n00:00:01,000 --> 00:00:02,500\r\n안녕\r\n")
        self.assertEqual(cues, [{"start": 1.0, "end": 2.5, "text": "안녕"}])

    def test_bad_srt(self):
        for body in ["1\n00:00:01 --> 00:00:02\nx", "garbage", "1\n00:61:00,000 --> 00:62:00,000\nx"]:
            with self.assertRaises(ComposeError):
                load_cues({"format": "srt", "text": body}, self.roots, Limits(), 6.0)

    def code(self, cues, duration=6.0, limits=Limits()):
        with self.assertRaises(ComposeError) as ctx:
            load_cues(cues, self.roots, limits, duration)
        return ctx.exception.code

    def test_timing_rules(self):
        self.assertEqual(self.code([{"start": 1, "end": 2, "text": "a"}, {"start": 1.5, "end": 3, "text": "b"}]),
                         "CUE_OVERLAP")
        self.assertEqual(self.code([{"start": 2, "end": 2, "text": "a"}]), "BAD_SUBTITLES")
        self.assertEqual(self.code([{"start": 7, "end": 8, "text": "a"}]), "CUE_AFTER_END")
        self.assertEqual(self.code([{"start": -1, "end": 1, "text": "a"}]), "BAD_SUBTITLES")
        self.assertEqual(self.code([]), "BAD_SUBTITLES")
        many = [{"start": i * 0.01, "end": i * 0.01 + 0.005, "text": "a"} for i in range(201)]
        self.assertEqual(self.code(many), "TOO_MANY_CUES")
        self.assertEqual(self.code([{"start": 0, "end": 1, "text": "가" * 201}]), "BAD_SUBTITLES")
        self.assertEqual(self.code([{"start": 0, "end": 1, "text": "a", "style": "x"}]), "BAD_SUBTITLES")

    def test_end_clipped_to_duration(self):
        cues, _ = load_cues([{"start": 5, "end": 99, "text": "끝"}], self.roots, Limits(), 6.0)
        self.assertEqual(cues[0].end, 6.0)

    def test_clean_text_strips_controls(self):
        self.assertEqual(clean_text("가‮나\x1b[31m다​\t라", Limits()), "가나[31m다라")
        self.assertEqual(clean_text("  첫 줄  \r\n\r\n 둘째 줄 ", Limits()), "첫 줄\n둘째 줄")
        with self.assertRaises(ComposeError):
            clean_text("\x00​\n", Limits())

    def test_subtitle_uri_must_be_inside_roots(self):
        self.assertEqual(self.code({"format": "srt", "uri": "/etc/passwd"}), "PATH_OUTSIDE_ROOTS")
        binary = self.root / "bin.srt"
        binary.write_bytes(b"\xff\xfe\x00\x01")
        self.assertEqual(self.code({"format": "srt", "uri": str(binary)}), "BAD_SUBTITLES")
        self.assertEqual(self.code({"format": "srt", "uri": str(FONT)}), "FILE_TOO_LARGE")


if __name__ == "__main__":
    unittest.main()
