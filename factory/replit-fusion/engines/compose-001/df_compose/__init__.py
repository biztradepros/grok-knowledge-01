"""DF-ENGINE-COMPOSE-001: 9:16 영상 + 한국어 자막 컴포지터.

공장 전체가 아니라 부품 하나다. 입력 영상 하나, 자막 목록 하나, 글꼴 하나를 받아
H.264/AAC MP4 와 ffprobe JSON, 결과 JSON 을 낸다.
"""

ENGINE_ID = "DF-ENGINE-COMPOSE-001"
ENGINE_VERSION = "0.1.0"
CONTRACT = "df.compose.v1"

from .errors import ComposeError  # noqa: E402
from .render import compose  # noqa: E402

__all__ = ["ENGINE_ID", "ENGINE_VERSION", "CONTRACT", "ComposeError", "compose"]
