"""DF-ENGINE-IDENTITY-001: 캐릭터 얼굴 일관성 평가기.

후보 이미지가 MASTER 와 같은 얼굴인지, 보호 대상(SOPHIE, F30 등)과 겹치지 않는지 점수를 낸다.
모델은 상업 이용 가능한 OpenCV zoo YuNet(MIT) + SFace(Apache-2.0) 만 쓴다.
insightface 계열(비상업 연구 전용)은 쓰지 않는다.

점수는 판정 보조다. MASTER LOCK 승인은 사람이 한다.
"""

ENGINE_ID = "DF-ENGINE-IDENTITY-001"
ENGINE_VERSION = "0.1.0"

from .evaluate import EvalError, Evaluator, Policy  # noqa: E402

__all__ = ["ENGINE_ID", "ENGINE_VERSION", "EvalError", "Evaluator", "Policy"]
