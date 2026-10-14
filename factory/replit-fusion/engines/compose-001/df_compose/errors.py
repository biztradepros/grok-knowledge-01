"""결과 JSON 에 그대로 실리는 구조화 오류."""


class ComposeError(Exception):
    """code 는 기계용, message 는 사람용, stage 는 어느 공정에서 멈췄는지."""

    def __init__(self, code, message, stage, detail=None):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.stage = stage
        self.detail = detail or {}

    def to_dict(self):
        return {
            "code": self.code,
            "message": self.message,
            "stage": self.stage,
            "detail": self.detail,
        }
