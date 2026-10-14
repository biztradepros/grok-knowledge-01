"""ffmpeg / ffprobe 호출.

- 셸을 쓰지 않는다. 인자는 목록으로만 넘긴다.
- 새 프로세스 그룹에서 실행하고, 시간 초과면 그룹 전체를 죽인다.
- 리눅스에서는 CPU 시간, 메모리, 출력 파일 크기를 rlimit 으로 묶는다.
- stderr 는 잘라서 줄 목록으로 돌려준다.
"""

import json
import os
import re
import shutil
import signal
import subprocess
import time

from .errors import ComposeError

try:
    import resource
except ImportError:  # pragma: no cover - 윈도우
    resource = None

STDERR_MAX_BYTES = 64 * 1024
STDERR_MAX_LINES = 60

# 입력 컨테이너와 코덱 허용 목록. probe 결과의 format_name 을 그대로 비교한다.
DEMUXERS = {
    "mov,mp4,m4a,3gp,3g2,mj2": "mov",
    "matroska,webm": "matroska",
}
VIDEO_CODECS = {"h264", "hevc", "vp8", "vp9", "av1", "mpeg4", "prores"}
AUDIO_CODECS = {"aac", "mp3", "opus", "vorbis", "pcm_s16le", "pcm_s24le", "flac", "alac"}
REQUIRED_ENCODERS = {"libx264", "aac"}
REQUIRED_FILTERS = {"scale", "crop", "fps", "overlay", "format", "setsar"}


def find_tool(name):
    path = shutil.which(name)
    if not path:
        raise ComposeError("TOOL_MISSING", f"{name} 를 찾을 수 없습니다.", "environment")
    return path


def _limiter(cpu_seconds, memory_bytes, output_bytes):
    def apply():
        if resource is None:
            return
        for lim, value in (
            (resource.RLIMIT_CPU, cpu_seconds),
            (resource.RLIMIT_AS, memory_bytes),
            (resource.RLIMIT_FSIZE, output_bytes),
            (resource.RLIMIT_CORE, 0),
        ):
            if value is not None:
                resource.setrlimit(lim, (int(value), int(value)))
    return apply


def run(args, stage, timeout, limits=None, cwd=None):
    """실행 결과 dict. 실패하면 ComposeError. stderr 는 구조화해서 detail 에 싣는다."""
    cpu = mem = out = None
    if limits is not None:
        # 입력·필터 스레드도 CPU 를 쓰므로 x264 스레드 수보다 넉넉히 준다. 벽시계 timeout 이 먼저 걸린다.
        cpu = int(timeout * (limits.ffmpeg_threads + 2) + 5)
        mem, out = limits.max_memory_bytes, limits.max_output_bytes
    started = time.monotonic()
    proc = subprocess.Popen(
        args,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=cwd,
        start_new_session=True,
        preexec_fn=_limiter(cpu, mem, out) if os.name == "posix" else None,
        env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LC_ALL": "C"},
    )
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        _kill_group(proc)
        stdout, stderr = proc.communicate()
        raise ComposeError("TIMEOUT", f"{stage} 단계가 {timeout}초 안에 끝나지 않았습니다.", stage,
                           {"timeout_seconds": timeout, "stderr": structure_stderr(stderr)})
    elapsed = round(time.monotonic() - started, 3)
    if proc.returncode != 0:
        code = "PROCESS_FAILED"
        if proc.returncode < 0:
            sig = -proc.returncode
            code = {signal.SIGXCPU: "CPU_LIMIT", signal.SIGXFSZ: "OUTPUT_SIZE_LIMIT",
                    signal.SIGKILL: "KILLED"}.get(sig, "SIGNALED")
        raise ComposeError(code, f"{stage} 단계의 {os.path.basename(args[0])} 가 실패했습니다.", stage,
                           {"returncode": proc.returncode, "elapsed_seconds": elapsed,
                            "stderr": structure_stderr(stderr)})
    return {"stdout": stdout, "stderr": structure_stderr(stderr), "elapsed_seconds": elapsed}


def _kill_group(proc):
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        proc.kill()


def structure_stderr(raw):
    raw = raw or b""
    truncated = len(raw) > STDERR_MAX_BYTES
    text = raw[-STDERR_MAX_BYTES:].decode("utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    errors = [line for line in lines if re.search(r"error|invalid|failed|cannot|unsupported", line, re.I)]
    return {
        "lines": lines[-STDERR_MAX_LINES:],
        "error_lines": errors[-20:],
        "line_count": len(lines),
        "truncated": truncated or len(lines) > STDERR_MAX_LINES,
    }


def check_toolchain(timeout=20):
    """필요한 인코더와 필터가 있는지. 없으면 렌더 전에 멈춘다."""
    ffmpeg, ffprobe = find_tool("ffmpeg"), find_tool("ffprobe")
    version = run([ffmpeg, "-hide_banner", "-version"], "environment", timeout)["stdout"].decode().splitlines()[0]
    enc = run([ffmpeg, "-hide_banner", "-encoders"], "environment", timeout)["stdout"].decode()
    flt = run([ffmpeg, "-hide_banner", "-filters"], "environment", timeout)["stdout"].decode()
    encoders = {line.split()[1] for line in enc.splitlines() if len(line.split()) > 1 and line.startswith(" ")}
    filters = {line.split()[1] for line in flt.splitlines() if len(line.split()) > 2 and line.startswith(" ")}
    missing = sorted((REQUIRED_ENCODERS - encoders) | (REQUIRED_FILTERS - filters))
    if missing:
        raise ComposeError("CODEC_UNAVAILABLE", "필요한 인코더나 필터가 없습니다.", "environment",
                           {"missing": missing, "ffmpeg": version})
    return {"ffmpeg": ffmpeg, "ffprobe": ffprobe, "ffmpeg_version": version,
            "encoders": sorted(REQUIRED_ENCODERS), "filters": sorted(REQUIRED_FILTERS)}


MP4_BOXES = {b"ftyp", b"moov", b"mdat", b"free", b"wide", b"skip"}
EBML_MAGIC = b"\x1a\x45\xdf\xa3"


def sniff(path):
    """ffmpeg 가 파일을 열기 전에 머리 바이트로 컨테이너를 정한다.

    확장자를 믿지 않는다. mp4 로 위장한 HLS/concat 재생목록이나 이미지 시퀀스 같은
    입력은 ffprobe 가 내용을 해석하기 전에 여기서 막힌다.
    """
    with open(path, "rb") as f:
        head = f.read(16)
    if len(head) >= 8 and head[4:8] in MP4_BOXES:
        return "mov"
    if head.startswith(EBML_MAGIC):
        return "matroska"
    raise ComposeError("CONTAINER_NOT_ALLOWED", "MP4/MOV 또는 Matroska/WebM 머리 바이트가 아닙니다.", "probe_input",
                       {"magic_hex": head[:8].hex()})


def probe(ffprobe, path, stage, timeout, demuxer=None, limits=None):
    args = [ffprobe, "-v", "error", "-protocol_whitelist", "file",
            "-probesize", "50000000", "-analyzeduration", "20000000"]
    if demuxer:
        args += ["-f", demuxer]
    args += ["-show_format", "-show_streams", "-of", "json", "file:" + str(path)]
    out = run(args, stage, timeout, limits=limits)
    try:
        return json.loads(out["stdout"].decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        raise ComposeError("PROBE_UNREADABLE", "ffprobe 출력을 읽을 수 없습니다.", stage)


def inspect_input(ffprobe, path, limits):
    """입력이 허용된 컨테이너/코덱이고 한도 안인지. 강제할 demuxer 이름도 돌려준다."""
    sniffed = sniff(path)
    info = probe(ffprobe, path, "probe_input", limits.probe_timeout_seconds, demuxer=sniffed, limits=limits)
    fmt = info.get("format", {})
    demuxer = DEMUXERS.get(fmt.get("format_name"))
    if demuxer != sniffed:
        raise ComposeError("CONTAINER_NOT_ALLOWED", "허용되지 않은 컨테이너입니다.", "probe_input",
                           {"format_name": fmt.get("format_name"), "allowed": sorted(DEMUXERS)})
    streams = info.get("streams", [])
    videos = [s for s in streams if s.get("codec_type") == "video" and not s.get("disposition", {}).get("attached_pic")]
    audios = [s for s in streams if s.get("codec_type") == "audio"]
    if not videos:
        raise ComposeError("NO_VIDEO_STREAM", "영상 스트림이 없습니다.", "probe_input")
    v = videos[0]
    if v.get("codec_name") not in VIDEO_CODECS:
        raise ComposeError("VIDEO_CODEC_NOT_ALLOWED", "허용되지 않은 영상 코덱입니다.", "probe_input",
                           {"codec": v.get("codec_name")})
    width, height = int(v.get("width") or 0), int(v.get("height") or 0)
    if width <= 0 or height <= 0 or width * height > limits.max_input_pixels:
        raise ComposeError("BAD_DIMENSIONS", "입력 해상도가 없거나 한도를 넘었습니다.", "probe_input",
                           {"width": width, "height": height})
    try:
        duration = float(fmt.get("duration") or v.get("duration") or 0)
    except ValueError:
        duration = 0.0
    if not (0 < duration <= limits.max_input_seconds):
        raise ComposeError("BAD_DURATION", "입력 길이가 없거나 한도를 넘었습니다.", "probe_input",
                           {"duration": duration, "max": limits.max_input_seconds})
    audio = None
    if audios:
        if audios[0].get("codec_name") not in AUDIO_CODECS:
            raise ComposeError("AUDIO_CODEC_NOT_ALLOWED", "허용되지 않은 오디오 코덱입니다.", "probe_input",
                               {"codec": audios[0].get("codec_name")})
        audio = audios[0]
    return {"demuxer": demuxer, "width": width, "height": height, "duration": duration,
            "video_codec": v.get("codec_name"), "audio_codec": audio and audio.get("codec_name"),
            "has_audio": audio is not None, "ffprobe": info}
