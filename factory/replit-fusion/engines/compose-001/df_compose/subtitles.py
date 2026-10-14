"""자막 입력 파싱과 정리.

받는 모양:
  [{"start": 0.0, "end": 1.5, "text": "..."}]              JSON 목록
  {"format": "srt", "text": "1\\n00:00:00,000 --> ..."}    SRT 본문
  {"format": "srt" | "json", "uri": "file:///..."}         허용 루트 안의 파일
"""

import hashlib
import json
import math
import re
import unicodedata
from dataclasses import dataclass

from .contract import resolve_uri
from .errors import ComposeError

TIME_RE = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2})[,.](\d{1,3})$")


@dataclass(frozen=True)
class Cue:
    start: float
    end: float
    text: str


def clean_text(text, limits):
    if not isinstance(text, str):
        raise ComposeError("BAD_SUBTITLES", "자막 text 가 문자열이 아닙니다.", "subtitles")
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    # 제어 문자, 방향 재정의 문자(Bidi override), 제로폭 문자를 지운다. 줄바꿈만 남긴다.
    kept = []
    for ch in text:
        cat = unicodedata.category(ch)
        if ch == "\n" or (cat[0] != "C" and ch not in "​‌‍⁠﻿"):
            kept.append(ch)
    lines = [" ".join(line.split()) for line in "".join(kept).split("\n")]
    lines = [line for line in lines if line]
    text = "\n".join(lines)
    if not text:
        raise ComposeError("BAD_SUBTITLES", "정리 후 빈 자막이 있습니다.", "subtitles")
    if len(text) > limits.max_cue_chars:
        raise ComposeError("BAD_SUBTITLES", "자막 한 줄이 너무 깁니다.", "subtitles",
                           {"chars": len(text), "max": limits.max_cue_chars})
    return text


def _time(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ComposeError("BAD_SUBTITLES", f"{name} 가 0 이상의 숫자가 아닙니다.", "subtitles")
    return round(float(value), 3)


def parse_srt(text):
    if not isinstance(text, str):
        raise ComposeError("BAD_SUBTITLES", "SRT 본문이 문자열이 아닙니다.", "subtitles")
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    cues = []
    for block in re.split(r"\n\s*\n", text.strip()):
        lines = block.split("\n")
        if lines and lines[0].strip().isdigit():
            lines = lines[1:]
        if not lines or "-->" not in lines[0]:
            raise ComposeError("BAD_SRT", "SRT 블록에 시간 줄이 없습니다.", "subtitles", {"block": block[:120]})
        left, right = [p.strip().split(" ")[0] for p in lines[0].split("-->", 1)]
        cues.append({"start": _srt_time(left), "end": _srt_time(right), "text": "\n".join(lines[1:])})
    return cues


def _srt_time(stamp):
    m = TIME_RE.match(stamp)
    if not m:
        raise ComposeError("BAD_SRT", "SRT 시간 형식이 아닙니다.", "subtitles", {"value": stamp[:40]})
    h, mi, s, ms = m.groups()
    if int(mi) > 59 or int(s) > 59:
        raise ComposeError("BAD_SRT", "SRT 시간 값이 범위를 벗어났습니다.", "subtitles", {"value": stamp})
    return int(h) * 3600 + int(mi) * 60 + int(s) + int(ms.ljust(3, "0")) / 1000


def load_cues(source, roots, limits, duration):
    """자막을 Cue 목록과 정규화 해시로 돌려준다. 끝 시각은 영상 길이로 자른다."""
    if isinstance(source, list):
        items = source
    elif isinstance(source, dict) and source.get("format") in ("srt", "json") and set(source) <= {"format", "text", "uri"}:
        if ("text" in source) == ("uri" in source):
            raise ComposeError("BAD_SUBTITLES", "text 와 uri 중 하나만 주어야 합니다.", "subtitles")
        if "uri" in source:
            path = resolve_uri(source["uri"], roots, "subtitles.uri", limits.max_subtitle_file_bytes)
            try:
                body = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                raise ComposeError("BAD_SUBTITLES", "자막 파일은 UTF-8 이어야 합니다.", "subtitles")
        else:
            body = source["text"]
            if not isinstance(body, str) or len(body.encode("utf-8")) > limits.max_subtitle_file_bytes:
                raise ComposeError("BAD_SUBTITLES", "자막 본문이 없거나 너무 큽니다.", "subtitles")
        if source["format"] == "srt":
            items = parse_srt(body)
        else:
            try:
                items = json.loads(body)
            except json.JSONDecodeError as exc:
                raise ComposeError("BAD_SUBTITLES", "자막 JSON 을 읽을 수 없습니다.", "subtitles", {"error": str(exc)})
            if not isinstance(items, list):
                raise ComposeError("BAD_SUBTITLES", "자막 JSON 은 목록이어야 합니다.", "subtitles")
    else:
        raise ComposeError("BAD_SUBTITLES", "subtitles_json_or_srt 모양이 계약과 다릅니다.", "subtitles")

    if not items:
        raise ComposeError("BAD_SUBTITLES", "자막이 하나도 없습니다.", "subtitles")
    if len(items) > limits.max_cues:
        raise ComposeError("TOO_MANY_CUES", "자막 개수가 한도를 넘었습니다.", "subtitles",
                           {"count": len(items), "max": limits.max_cues})

    cues = []
    for i, item in enumerate(items):
        if not isinstance(item, dict) or set(item) != {"start", "end", "text"}:
            raise ComposeError("BAD_SUBTITLES", f"{i}번 자막은 start, end, text 만 가져야 합니다.", "subtitles")
        start, end = _time(item["start"], f"{i}.start"), _time(item["end"], f"{i}.end")
        if end <= start:
            raise ComposeError("BAD_SUBTITLES", f"{i}번 자막의 end 가 start 보다 늦지 않습니다.", "subtitles")
        if start >= duration:
            raise ComposeError("CUE_AFTER_END", f"{i}번 자막이 영상이 끝난 뒤에 시작합니다.", "subtitles",
                               {"start": start, "duration": duration})
        cues.append(Cue(start, min(end, round(duration, 3)), clean_text(item["text"], limits)))

    cues.sort(key=lambda c: c.start)
    for a, b in zip(cues, cues[1:]):
        if b.start < a.end:
            raise ComposeError("CUE_OVERLAP", "자막 시간이 겹칩니다.", "subtitles",
                               {"first": [a.start, a.end], "second": [b.start, b.end]})

    blob = json.dumps([c.__dict__ for c in cues], ensure_ascii=False, separators=(",", ":"))
    return cues, hashlib.sha256(blob.encode("utf-8")).hexdigest()
