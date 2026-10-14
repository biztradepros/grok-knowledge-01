"""얼굴 검출 → 정렬 → 128차원 특징 → 코사인 유사도 → 판정.

판정 구간(Policy)은 아직 AI 생성 얼굴로 보정하지 않은 잠정값이다. 보정 절차는 STUDIO_SPEC.md 의
TEST PLAN T-3 에 있다. 결과에는 항상 policy 값을 함께 남겨, 나중에 기준을 바꿔도 다시 판정할 수 있게 한다.

얼굴 특징 벡터는 생체 정보에 가깝다. 기본값으로 결과에 남기지 않는다.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
import numpy as np

from . import ENGINE_ID, ENGINE_VERSION

HERE = Path(__file__).resolve().parent
MODELS = json.loads((HERE.parent / "models.json").read_text())
MAX_IMAGE_BYTES = 30 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000


class EvalError(Exception):
    def __init__(self, code, message, detail=None):
        super().__init__(f"{code}: {message}")
        self.code, self.message, self.detail = code, message, detail or {}

    def to_dict(self):
        return {"code": self.code, "message": self.message, "detail": self.detail}


@dataclass(frozen=True)
class Policy:
    # 같은 캐릭터 판정 (후보 vs MASTER, 최댓값 기준)
    same_pass: float = 0.55        # 이 이상이면 자동 통과 후보 (그래도 사람 승인 필요)
    same_review: float = 0.363     # SFace 상류 기준. 이 이상 same_pass 미만은 사람 검토
    # 보호 대상과의 분리 판정 (후보 vs SOPHIE/F30 등, 최댓값 기준)
    protected_max: float = 0.30    # 이 값을 넘으면 보호 대상과 너무 닮음 → 차단
    min_face_px: int = 96          # 얼굴 상자 짧은 변
    min_det_score: float = 0.90
    calibrated: bool = False       # AI 생성 얼굴로 보정 전


def sha256_file(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class Evaluator:
    def __init__(self, model_dir, policy=Policy()):
        self.policy = policy
        model_dir = Path(model_dir)
        paths = {}
        for m in MODELS["models"]:
            p = model_dir / Path(m["path"]).name
            if not p.is_file():
                raise EvalError("MODEL_MISSING", f"{p.name} 가 없습니다.", {"expected_sha256": m["sha256"]})
            actual = sha256_file(p)
            if actual != m["sha256"]:
                raise EvalError("MODEL_HASH_MISMATCH", f"{p.name} 해시가 다릅니다.",
                                {"expected": m["sha256"], "actual": actual})
            paths[m["id"]] = str(p)
        self.detector = cv2.FaceDetectorYN.create(paths["yunet"], "", (320, 320), 0.6, 0.3, 50)
        self.recognizer = cv2.FaceRecognizerSF.create(paths["sface"], "")
        self.model_hashes = {m["id"]: m["sha256"] for m in MODELS["models"]}

    # --- 한 장 -------------------------------------------------------------

    def load(self, path):
        path = Path(path)
        if not path.is_file():
            raise EvalError("IMAGE_MISSING", "이미지가 없습니다.", {"file": path.name})
        size = path.stat().st_size
        if size == 0 or size > MAX_IMAGE_BYTES:
            raise EvalError("IMAGE_SIZE", "이미지 크기가 0 이거나 한도를 넘습니다.", {"bytes": size})
        data = np.frombuffer(path.read_bytes(), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise EvalError("IMAGE_UNREADABLE", "이미지를 읽을 수 없습니다.", {"file": path.name})
        if img.shape[0] * img.shape[1] > MAX_IMAGE_PIXELS:
            raise EvalError("IMAGE_TOO_LARGE", "픽셀 수가 한도를 넘습니다.", {"shape": list(img.shape)})
        return img

    def face(self, img, name="image"):
        """가장 큰 얼굴 하나의 (특징, 정보). 얼굴이 없거나 작으면 오류."""
        h, w = img.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        if faces is None or len(faces) == 0:
            raise EvalError("NO_FACE", "얼굴을 찾지 못했습니다.", {"image": name})
        faces = sorted(faces, key=lambda f: f[2] * f[3], reverse=True)
        best = faces[0]
        x, y, fw, fh, score = float(best[0]), float(best[1]), float(best[2]), float(best[3]), float(best[14])
        info = {"faces_detected": int(len(faces)), "bbox": [round(x), round(y), round(fw), round(fh)],
                "det_score": round(score, 4), "short_side_px": round(min(fw, fh))}
        if score < self.policy.min_det_score:
            raise EvalError("LOW_DET_SCORE", "얼굴 검출 신뢰도가 낮습니다.", {"image": name, **info})
        if min(fw, fh) < self.policy.min_face_px:
            raise EvalError("FACE_TOO_SMALL", "얼굴이 너무 작습니다. 얼굴이 크게 나온 컷을 쓰세요.", {"image": name, **info})
        aligned = self.recognizer.alignCrop(img, best)
        feat = self.recognizer.feature(aligned).astype(np.float32).copy()
        return feat, info

    def all_faces(self, img):
        """시험용: 이미지 안의 모든 얼굴 특징."""
        h, w = img.shape[:2]
        self.detector.setInputSize((w, h))
        _, faces = self.detector.detect(img)
        out = []
        for f in faces if faces is not None else []:
            if f[14] >= self.policy.min_det_score and min(f[2], f[3]) >= self.policy.min_face_px:
                out.append(self.recognizer.feature(self.recognizer.alignCrop(img, f)).astype(np.float32).copy())
        return out

    def cosine(self, a, b):
        return float(self.recognizer.match(a, b, cv2.FaceRecognizerSF_FR_COSINE))

    # --- 판정 --------------------------------------------------------------

    def evaluate(self, masters, candidates, protected=None):
        """masters: [경로], candidates: [경로], protected: {이름: [경로]}.

        반환: 결과 dict. 개별 이미지 오류는 그 후보의 verdict=ERROR 로 남기고 계속한다.
        MASTER 나 보호 대상 이미지 오류는 전체를 멈춘다.
        """
        p = self.policy
        master_feats, master_meta = [], []
        for m in masters:
            feat, info = self.face(self.load(m), Path(m).name)
            master_feats.append(feat)
            master_meta.append({"file": Path(m).name, "sha256": sha256_file(m), **info})
        if not master_feats:
            raise EvalError("NO_MASTER", "MASTER 이미지가 없습니다.")
        prot = {}
        for name, files in (protected or {}).items():
            prot[name] = []
            for f in files:
                feat, _ = self.face(self.load(f), Path(f).name)
                prot[name].append(feat)

        rows = []
        for c in candidates:
            row = {"file": Path(c).name}
            try:
                row["sha256"] = sha256_file(c)
                feat, info = self.face(self.load(c), Path(c).name)
                row.update(info)
                sims = [self.cosine(feat, mf) for mf in master_feats]
                row["master_cosine_max"] = round(max(sims), 4)
                row["master_cosine_mean"] = round(sum(sims) / len(sims), 4)
                prot_scores = {name: round(max(self.cosine(feat, pf) for pf in feats), 4)
                               for name, feats in prot.items() if feats}
                row["protected_cosine_max"] = prot_scores
                row["verdict"], row["reasons"] = self._verdict(row["master_cosine_max"], prot_scores)
            except EvalError as exc:
                row["verdict"], row["error"] = "ERROR", exc.to_dict()
            rows.append(row)

        counts = {}
        for r in rows:
            counts[r["verdict"]] = counts.get(r["verdict"], 0) + 1
        return {
            "engine": {"id": ENGINE_ID, "version": ENGINE_VERSION},
            "models": self.model_hashes,
            "policy": asdict(p),
            "masters": master_meta,
            "protected": {k: len(v) for k, v in prot.items()},
            "candidates": rows,
            "summary": counts,
            "note": "점수는 판정 보조. MASTER LOCK 은 사람 승인으로만 한다. calibrated=false 이면 구간은 잠정값.",
        }

    def _verdict(self, master_max, prot_scores):
        p, reasons = self.policy, []
        blocked = [k for k, v in prot_scores.items() if v > p.protected_max]
        if blocked:
            reasons.append(f"보호 대상과 유사: {', '.join(blocked)}")
            return "BLOCK_PROTECTED", reasons
        if master_max >= p.same_pass:
            return "PASS_CANDIDATE", reasons
        if master_max >= p.same_review:
            reasons.append("MASTER 와의 유사도가 검토 구간")
            return "REVIEW", reasons
        reasons.append("MASTER 와 다른 얼굴로 판단")
        return "FAIL_DRIFT", reasons
