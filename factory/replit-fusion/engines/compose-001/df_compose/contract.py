"""요청 계약 df.compose.v1 검증.

요청은 신뢰하지 않는다. 경로, 숫자, 문자열을 모두 여기서 검사한 뒤에만
렌더 단계로 넘긴다. 렌더 단계는 이 모듈이 돌려준 값만 쓴다.
"""

import hashlib
import json
import math
import os
import re
import stat
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlparse

from . import CONTRACT
from .errors import ComposeError


@dataclass(frozen=True)
class Limits:
    max_input_bytes: int = 500 * 1024 * 1024
    max_input_seconds: float = 180.0
    max_input_pixels: int = 4096 * 4096
    min_output_side: int = 128
    max_output_side: int = 2160
    min_fps: int = 12
    max_fps: int = 60
    max_cues: int = 200
    max_cue_chars: int = 200
    max_cue_lines: int = 3
    max_subtitle_file_bytes: int = 1024 * 1024
    max_font_bytes: int = 30 * 1024 * 1024
    timeout_seconds: float = 300.0
    probe_timeout_seconds: float = 30.0
    max_memory_bytes: int = 4 * 1024 * 1024 * 1024
    max_output_bytes: int = 1024 * 1024 * 1024
    # x264 threads > 1 이면 이 ffmpeg 6.1 빌드에서 가끔 프레임 하나가 달라진다(실측 1/17~1/60).
    # 1 이면 100/100 같은 해시. 속도가 더 필요하면 올리되 결과는 결정론적이지 않다.
    ffmpeg_threads: int = 1


ALLOWED_FONT_LICENSES = {"OFL-1.1", "Apache-2.0", "MIT", "UFL-1.0"}
JOB_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{2,95}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

DEFAULT_STYLE = {
    "font_size_ratio": 0.045,
    "fill": "#FFFFFF",
    "stroke": "#000000",
    "stroke_ratio": 0.08,
    "line_spacing": 1.25,
}


@dataclass
class SafeArea:
    top: float
    bottom: float
    left: float
    right: float

    def box(self, width, height):
        """출력 좌표계의 안전 영역 (x0, y0, x1, y1)."""
        return (
            int(round(self.left * width)),
            int(round(self.top * height)),
            int(round(width - self.right * width)),
            int(round(height - self.bottom * height)),
        )


@dataclass
class FontAsset:
    path: Path
    sha256: str
    license: str
    license_path: Path


@dataclass
class Request:
    job_id: str
    video_path: Path
    subtitles_source: object
    output_size: tuple
    output_fps: int
    safe_area: SafeArea
    font: FontAsset
    style: dict
    raw: dict = field(repr=False)

    def canonical_sha256(self):
        blob = json.dumps(self.raw, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def sha256_file(path, chunk=1024 * 1024):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def resolve_uri(uri, roots, what, max_bytes):
    """file:// 또는 경로만 받는다. 실제 경로가 허용 루트 안의 일반 파일이어야 한다.

    심볼릭 링크는 따라간 최종 경로로 판정하므로 루트 밖을 가리키면 거절된다.
    """
    if not isinstance(uri, str) or not uri or len(uri) > 4096 or "\x00" in uri:
        raise ComposeError("BAD_URI", f"{what}: 문자열 경로가 아닙니다.", "validate")
    parsed = urlparse(uri)
    if parsed.scheme in ("", "file"):
        if parsed.scheme == "file":
            if parsed.netloc not in ("", "localhost"):
                raise ComposeError("SCHEME_NOT_ALLOWED", f"{what}: 원격 file 호스트는 받지 않습니다.", "validate")
            raw_path = unquote(parsed.path)
        else:
            raw_path = uri
    else:
        raise ComposeError(
            "SCHEME_NOT_ALLOWED",
            f"{what}: '{parsed.scheme}' 주소는 받지 않습니다. 상위 수집기가 파일로 내려받아 넘겨야 합니다.",
            "validate",
            {"scheme": parsed.scheme},
        )
    if not roots:
        raise ComposeError("NO_ALLOWED_ROOTS", "허용 루트가 설정되지 않았습니다.", "validate")
    try:
        real = Path(os.path.realpath(raw_path))
    except (OSError, ValueError) as exc:
        raise ComposeError("BAD_URI", f"{what}: 경로를 해석할 수 없습니다.", "validate", {"error": str(exc)})
    if not any(_is_within(real, r) for r in roots):
        raise ComposeError("PATH_OUTSIDE_ROOTS", f"{what}: 허용 루트 밖의 경로입니다.", "validate",
                           {"resolved": str(real)})
    try:
        st = real.stat()
    except OSError:
        raise ComposeError("NOT_FOUND", f"{what}: 파일이 없습니다.", "validate", {"resolved": str(real)})
    if not stat.S_ISREG(st.st_mode):
        raise ComposeError("NOT_REGULAR_FILE", f"{what}: 일반 파일이 아닙니다.", "validate")
    if st.st_size == 0:
        raise ComposeError("EMPTY_FILE", f"{what}: 빈 파일입니다.", "validate")
    if st.st_size > max_bytes:
        raise ComposeError("FILE_TOO_LARGE", f"{what}: 파일이 너무 큽니다.", "validate",
                           {"bytes": st.st_size, "max_bytes": max_bytes})
    return real


def _is_within(path, root):
    root = Path(os.path.realpath(root))
    return path == root or root in path.parents


def _number(value, name, lo, hi, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ComposeError("BAD_FIELD", f"{name}: 숫자가 아닙니다.", "validate")
    if not math.isfinite(value) or value < lo or value > hi:
        raise ComposeError("BAD_FIELD", f"{name}: {lo}~{hi} 범위를 벗어났습니다.", "validate", {"value": value})
    if integer and int(value) != value:
        raise ComposeError("BAD_FIELD", f"{name}: 정수가 아닙니다.", "validate")
    return int(value) if integer else float(value)


def parse_request(raw, roots, limits=Limits()):
    if not isinstance(raw, dict):
        raise ComposeError("BAD_REQUEST", "요청은 JSON 객체여야 합니다.", "validate")
    allowed = {"contract", "job_id", "video_uri", "subtitles_json_or_srt", "output_size",
               "output_fps", "safe_area", "font_asset", "style"}
    unknown = sorted(set(raw) - allowed)
    if unknown:
        raise ComposeError("UNKNOWN_FIELD", "계약에 없는 필드가 있습니다.", "validate", {"fields": unknown})
    if raw.get("contract", CONTRACT) != CONTRACT:
        raise ComposeError("CONTRACT_MISMATCH", f"contract 는 {CONTRACT} 여야 합니다.", "validate")

    job_id = raw.get("job_id")
    if not isinstance(job_id, str) or not JOB_ID_RE.match(job_id) or ".." in job_id:
        raise ComposeError("BAD_JOB_ID", "job_id 는 영문, 숫자, '_', '-', '.' 3~96자여야 합니다.", "validate")

    video_path = resolve_uri(raw.get("video_uri"), roots, "video_uri", limits.max_input_bytes)

    size = raw.get("output_size")
    if not isinstance(size, (list, tuple)) or len(size) != 2:
        raise ComposeError("BAD_FIELD", "output_size 는 [width, height] 여야 합니다.", "validate")
    w = _number(size[0], "output_size.width", limits.min_output_side, limits.max_output_side, True)
    h = _number(size[1], "output_size.height", limits.min_output_side, limits.max_output_side, True)
    if w % 2 or h % 2:
        raise ComposeError("BAD_FIELD", "output_size 는 짝수여야 합니다 (yuv420p).", "validate")

    fps = _number(raw.get("output_fps"), "output_fps", limits.min_fps, limits.max_fps, True)

    sa = raw.get("safe_area", {"top": 0.1, "bottom": 0.18, "left": 0.06, "right": 0.06})
    if not isinstance(sa, dict) or set(sa) != {"top", "bottom", "left", "right"}:
        raise ComposeError("BAD_FIELD", "safe_area 는 top, bottom, left, right 비율이어야 합니다.", "validate")
    safe = SafeArea(**{k: _number(sa[k], f"safe_area.{k}", 0.0, 0.45) for k in sa})

    font_raw = raw.get("font_asset")
    if not isinstance(font_raw, dict) or set(font_raw) != {"uri", "sha256", "license", "license_uri"}:
        raise ComposeError("BAD_FONT", "font_asset 는 uri, sha256, license, license_uri 가 필요합니다.", "validate")
    if font_raw["license"] not in ALLOWED_FONT_LICENSES:
        raise ComposeError("FONT_LICENSE_NOT_ALLOWED", "허용되지 않은 글꼴 라이선스입니다.", "validate",
                           {"license": font_raw["license"], "allowed": sorted(ALLOWED_FONT_LICENSES)})
    if not isinstance(font_raw["sha256"], str) or not SHA256_RE.match(font_raw["sha256"]):
        raise ComposeError("BAD_FONT", "font_asset.sha256 형식이 아닙니다.", "validate")
    font_path = resolve_uri(font_raw["uri"], roots, "font_asset.uri", limits.max_font_bytes)
    if font_path.suffix.lower() not in (".ttf", ".otf"):
        raise ComposeError("BAD_FONT", "글꼴은 .ttf 또는 .otf 여야 합니다.", "validate")
    license_path = resolve_uri(font_raw["license_uri"], roots, "font_asset.license_uri", 1024 * 1024)
    actual = sha256_file(font_path)
    if actual != font_raw["sha256"]:
        raise ComposeError("FONT_HASH_MISMATCH", "글꼴 파일 해시가 선언과 다릅니다.", "validate",
                           {"declared": font_raw["sha256"], "actual": actual})
    font = FontAsset(font_path, actual, font_raw["license"], license_path)

    style = dict(DEFAULT_STYLE)
    st = raw.get("style", {})
    if not isinstance(st, dict) or set(st) - set(DEFAULT_STYLE):
        raise ComposeError("BAD_FIELD", "style 에 알 수 없는 키가 있습니다.", "validate")
    for k in ("fill", "stroke"):
        if k in st:
            if not isinstance(st[k], str) or not COLOR_RE.match(st[k]):
                raise ComposeError("BAD_FIELD", f"style.{k} 는 #RRGGBB 여야 합니다.", "validate")
            style[k] = st[k].upper()
    for k, lo, hi in (("font_size_ratio", 0.015, 0.12), ("stroke_ratio", 0.0, 0.2), ("line_spacing", 1.0, 2.0)):
        if k in st:
            style[k] = _number(st[k], f"style.{k}", lo, hi)

    subs = raw.get("subtitles_json_or_srt")
    if subs is None:
        raise ComposeError("BAD_SUBTITLES", "subtitles_json_or_srt 가 필요합니다.", "validate")

    return Request(job_id, video_path, subs, (w, h), fps, safe, font, style, raw)
