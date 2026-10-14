"""DF-ENGINE-IDENTITY-001 시험.

DF_ID_MODELS: YuNet/SFace onnx 가 있는 폴더 (없으면 전체 건너뜀)
DF_ID_SMOKE_DIR: opencv_zoo 예시 이미지 폴더 (largest_selfie.jpg). 없으면 얼굴 시험만 건너뜀.
예시 이미지는 실존 인물 사진이라 저장소에 넣지 않는다. 받는 주소는 README 에 있다.
"""

import itertools
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from df_identity import EvalError, Evaluator, Policy  # noqa: E402
from df_identity.__main__ import main as cli_main  # noqa: E402

MODELS = os.environ.get("DF_ID_MODELS")
SMOKE = os.environ.get("DF_ID_SMOKE_DIR")


@unittest.skipUnless(MODELS, "DF_ID_MODELS 없음")
class BasicTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="dfid-"))
        self.ev = Evaluator(MODELS)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_model_hash_is_checked(self):
        bad = self.tmp / "models"
        bad.mkdir()
        for f in Path(MODELS).glob("*.onnx"):
            shutil.copy(f, bad / f.name)
        target = next(bad.glob("face_detection_yunet*.onnx"))
        target.write_bytes(target.read_bytes() + b"x")
        with self.assertRaises(EvalError) as ctx:
            Evaluator(bad)
        self.assertEqual(ctx.exception.code, "MODEL_HASH_MISMATCH")

    def test_no_face(self):
        img = np.tile(np.linspace(0, 255, 640, dtype=np.uint8), (480, 1))
        path = self.tmp / "gradient.png"
        cv2.imwrite(str(path), cv2.cvtColor(img, cv2.COLOR_GRAY2BGR))
        with self.assertRaises(EvalError) as ctx:
            self.ev.face(self.ev.load(path))
        self.assertEqual(ctx.exception.code, "NO_FACE")

    def test_unreadable_and_missing(self):
        junk = self.tmp / "junk.png"
        junk.write_bytes(b"not an image")
        for path, code in ((junk, "IMAGE_UNREADABLE"), (self.tmp / "none.png", "IMAGE_MISSING")):
            with self.assertRaises(EvalError) as ctx:
                self.ev.load(path)
            self.assertEqual(ctx.exception.code, code)

    def test_verdict_bands(self):
        v = self.ev._verdict
        p = Policy()
        self.assertEqual(v(p.same_pass, {})[0], "PASS_CANDIDATE")
        self.assertEqual(v(p.same_review, {})[0], "REVIEW")
        self.assertEqual(v(p.same_review - 0.01, {})[0], "FAIL_DRIFT")
        self.assertEqual(v(0.9, {"SOPHIE": p.protected_max + 0.01})[0], "BLOCK_PROTECTED")
        self.assertEqual(v(0.9, {"SOPHIE": p.protected_max})[0], "PASS_CANDIDATE")

    def test_cli_usage_error(self):
        self.assertEqual(cli_main(["--models", MODELS, "--master", "a", "--candidate", "b",
                                   "--protected", "noequals"]), 64)


@unittest.skipUnless(MODELS and SMOKE, "DF_ID_MODELS / DF_ID_SMOKE_DIR 없음")
class SmokeFaceTests(unittest.TestCase):
    """실제 얼굴로 파이프라인이 동작하는지. 보정이 아니라 기계적 동작 확인이다."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="dfid-smoke-"))
        cls.ev = Evaluator(MODELS)
        img = cls.ev.load(Path(SMOKE) / "largest_selfie.jpg")
        _, info = cls.ev.face(img)
        x, y, w, h = info["bbox"]
        pad = int(max(w, h) * 0.8)
        cls.crop = img[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad]
        cls.master = cls.tmp / "master.png"
        cv2.imwrite(str(cls.master), cls.crop)
        cls.feats = cls.ev.all_faces(img)
        # 다른 사람: 원본에서 가장 큰 얼굴을 가린 이미지의 다음 얼굴
        masked = img.copy()
        masked[y:y + h, x:x + w] = 0
        cls.other = cls.tmp / "other.png"
        cv2.imwrite(str(cls.other), masked)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def write(self, name, img):
        p = self.tmp / name
        cv2.imwrite(str(p), img)
        return p

    def test_same_face_under_transforms_passes(self):
        c = self.crop
        variants = {
            "flip.png": cv2.flip(c, 1),
            "bright.png": cv2.convertScaleAbs(c, alpha=1.0, beta=30),
            "jpeg.jpg": cv2.imdecode(cv2.imencode(".jpg", c, [cv2.IMWRITE_JPEG_QUALITY, 30])[1], 1),
            "rot.png": cv2.warpAffine(c, cv2.getRotationMatrix2D((c.shape[1] / 2, c.shape[0] / 2), 8, 1),
                                      (c.shape[1], c.shape[0])),
        }
        paths = [str(self.write(k, v)) for k, v in variants.items()]
        r = self.ev.evaluate([str(self.master)], paths)
        for row in r["candidates"]:
            self.assertEqual(row["verdict"], "PASS_CANDIDATE", row)
            self.assertGreater(row["master_cosine_max"], 0.8, row)

    def test_different_people_are_below_upstream_threshold(self):
        self.assertGreaterEqual(len(self.feats), 3)
        for a, b in itertools.combinations(self.feats, 2):
            self.assertLess(self.ev.cosine(a, b), Policy().same_review)

    def test_other_person_is_drift(self):
        r = self.ev.evaluate([str(self.master)], [str(self.other)])
        self.assertEqual(r["candidates"][0]["verdict"], "FAIL_DRIFT", r["candidates"][0])

    def test_protected_identity_blocks(self):
        flip = self.write("flip_p.png", cv2.flip(self.crop, 1))
        r = self.ev.evaluate([str(self.other)], [str(flip)], protected={"SOPHIE": [str(self.master)]})
        self.assertEqual(r["candidates"][0]["verdict"], "BLOCK_PROTECTED", r["candidates"][0])

    def test_small_face_is_rejected_not_scored(self):
        small = self.write("small.png", cv2.resize(self.crop, None, fx=0.4, fy=0.4))
        r = self.ev.evaluate([str(self.master)], [str(small)])
        row = r["candidates"][0]
        self.assertEqual(row["verdict"], "ERROR")
        self.assertEqual(row["error"]["code"], "FACE_TOO_SMALL")

    def test_result_has_no_embeddings(self):
        r = self.ev.evaluate([str(self.master)], [str(self.master)])
        text = repr(r)
        self.assertNotIn("array(", text)
        self.assertEqual(r["policy"]["calibrated"], False)


if __name__ == "__main__":
    unittest.main()
