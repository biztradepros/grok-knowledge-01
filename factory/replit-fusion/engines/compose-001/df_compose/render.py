"""렌더 공정.

validate → probe_input → subtitles → rasterize → write_track(APNG) → render → verify → commit

사용자 문자열은 ffmpeg 인자나 필터 문자열에 들어가지 않는다. 자막 글자는 Pillow 로
PNG 로 그리고, 자막 전체를 APNG 하나로 묶어 overlay 로 얹는다. 필터 문자열에는 검증된 정수와
실수만 들어간다.

출력은 임시 폴더에서 만들고, 검사가 모두 통과한 뒤에만 <out_dir>/<job_id> 로
이름을 바꾼다. 실패하면 임시 폴더를 지우고 <out_dir>/_failed/ 에 결과 JSON 만 남긴다.
"""

import json
import math
import os
import platform
import shutil
import statistics
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFont

from . import CONTRACT, ENGINE_ID, ENGINE_VERSION
from .contract import Limits, parse_request, sha256_file
from .errors import ComposeError
from .media import check_toolchain, inspect_input, probe, run
from .subtitles import load_cues

AUDIO_RATE = 48000


def _utc():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _hex_rgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def _engine_commit():
    here = Path(__file__).resolve().parent
    try:
        out = subprocess.run(["git", "-C", str(here), "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
        dirty = subprocess.run(["git", "-C", str(here), "status", "--porcelain", "--", "."],
                               capture_output=True, text=True, timeout=5)
        if out.returncode == 0:
            return {"git_commit": out.stdout.strip(), "dirty": bool(dirty.stdout.strip())}
    except (OSError, subprocess.SubprocessError):
        pass
    return {"git_commit": None, "dirty": None}


# --- 글자 ---------------------------------------------------------------

def missing_glyphs(font, text):
    """글꼴에 없는 글자. Pillow 가 .notdef 로 그리는 모양과 같으면 없는 것으로 본다(휴리스틱)."""
    notdef = font.getmask("\U0010FFFD")
    sig = (notdef.size, bytes(notdef))
    missing = []
    for ch in sorted(set(text)):
        if ch.isspace():
            continue
        m = font.getmask(ch)
        if (m.size, bytes(m)) == sig:
            missing.append(ch)
    return missing


def wrap(draw, font, text, max_width, stroke):
    lines = []
    for para in text.split("\n"):
        current = ""
        for word in para.split(" "):
            trial = word if not current else current + " " + word
            if draw.textlength(trial, font=font) + 2 * stroke <= max_width:
                current = trial
                continue
            if current:
                lines.append(current)
            current = ""
            # 한 단어가 너비보다 길면 글자 단위로 자른다.
            for ch in word:
                if draw.textlength(current + ch, font=font) + 2 * stroke <= max_width:
                    current += ch
                else:
                    if current:
                        lines.append(current)
                    current = ch
        if current:
            lines.append(current)
    return lines


def cue_frame(index, start, end, fps):
    """자막이 걸리는 출력 프레임 중 가운데 프레임 번호.

    경계에서 1ms 안쪽에 있는 프레임만 센다. 경계와 프레임 시각이 겹치면 반올림에 따라 보일 수도,
    안 보일 수도 있기 때문이다. 걸리는 프레임이 없으면 그 자막은 화면에 나오지 않는다.
    """
    first = math.ceil((start + 0.001) * fps)
    last = math.floor((end - 0.001) * fps)
    if last < first:
        raise ComposeError("CUE_SHORTER_THAN_FRAME", f"{index}번 자막이 출력 프레임 하나도 덮지 못합니다.",
                           "rasterize", {"start": start, "end": end, "fps": fps})
    return (first + last) // 2


def rasterize(cues, font_path, size, safe_area, style, limits, work, fps):
    width, height = size
    x0, y0, x1, y1 = safe_area.box(width, height)
    box_w, box_h = x1 - x0, y1 - y0
    if box_w < 32 or box_h < 32:
        raise ComposeError("SAFE_AREA_TOO_SMALL", "안전 영역이 너무 작습니다.", "rasterize")
    font_px = max(10, int(round(style["font_size_ratio"] * height)))
    stroke = int(round(style["stroke_ratio"] * font_px))
    try:
        font = ImageFont.truetype(str(font_path), font_px)
    except OSError as exc:
        raise ComposeError("FONT_UNREADABLE", "글꼴을 열 수 없습니다.", "rasterize", {"error": str(exc)})
    missing = missing_glyphs(font, "".join(c.text for c in cues))
    if missing:
        raise ComposeError("GLYPH_MISSING", "글꼴에 없는 글자가 있습니다.", "rasterize",
                           {"chars": missing[:50], "count": len(missing)})

    fill, stroke_fill = _hex_rgb(style["fill"]), _hex_rgb(style["stroke"])
    scratch = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    ascent, descent = font.getmetrics()
    line_h = int(round((ascent + descent) * style["line_spacing"]))
    out = []
    for i, cue in enumerate(cues):
        frame_no = cue_frame(i, cue.start, cue.end, fps)
        lines = wrap(scratch, font, cue.text, box_w, stroke)
        if len(lines) > limits.max_cue_lines:
            raise ComposeError("CUE_TOO_LONG_FOR_AREA", f"{i}번 자막이 {limits.max_cue_lines}줄을 넘습니다.",
                               "rasterize", {"lines": len(lines)})
        block_h = line_h * (len(lines) - 1) + ascent + descent + 2 * stroke
        if block_h > box_h:
            raise ComposeError("CUE_TOO_LONG_FOR_AREA", f"{i}번 자막이 안전 영역 높이를 넘습니다.", "rasterize")
        img = Image.new("RGBA", (box_w, block_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        for n, line in enumerate(lines):
            lw = draw.textlength(line, font=font)
            draw.text(((box_w - lw) / 2, stroke + n * line_h), line, font=font, fill=fill + (255,),
                      stroke_width=stroke, stroke_fill=stroke_fill + (255,))
        x, y = x0, y1 - block_h
        path = work / f"cue_{i:03d}.png"
        img.save(path, format="PNG", optimize=False)
        out.append({"index": i, "path": path, "x": x, "y": y, "w": box_w, "h": block_h,
                    "start": cue.start, "end": cue.end, "lines": lines, "frame": frame_no})
    return out, {"font_px": font_px, "stroke_px": stroke, "safe_box": [x0, y0, x1, y1]}


def write_track(overlays, duration, work):
    """자막 전체를 APNG 하나로 만든다. 돌려주는 값: (경로, 얹을 x, 얹을 y).

    - 자막마다 ffmpeg 입력을 따로 만들면 입력마다 스레드와 디코더가 생겨 자막 수십 개에서
      주소 공간 한도에 걸린다(실측: 200개 중 38번째에서 EAGAIN).
    - concat 목록으로 PNG 를 묶으면 타임스탬프가 1/25초로 반올림된다(실측: 0.3초 → 0.32초).
      정밀도를 바꾸는 option 지시어는 -safe 1 에서 막혀 있다.
    - APNG 는 프레임마다 ms 지연을 담고 ffmpeg 이 1/100000 초 단위로 읽는다. 입력은 이 파일 하나다.
    캔버스는 화면 전체가 아니라 자막 띠(안전 영역 너비 × 가장 높은 자막) 크기라 메모리가 작다.
    """
    band_w = overlays[0]["w"]
    band_h = max(ov["h"] for ov in overlays)
    band_x, band_y = overlays[0]["x"], max(ov["y"] + ov["h"] for ov in overlays) - band_h
    blank = Image.new("RGBA", (band_w, band_h), (0, 0, 0, 0))
    frames, durations, t_ms = [], [], 0
    for ov in overlays:
        start_ms, end_ms = int(round(ov["start"] * 1000)), int(round(ov["end"] * 1000))
        if start_ms > t_ms:
            frames.append(blank)
            durations.append(start_ms - t_ms)
        frame = blank.copy()
        with Image.open(ov["path"]) as cue:
            frame.paste(cue.convert("RGBA"), (ov["x"] - band_x, ov["y"] - band_y))
        frames.append(frame)
        durations.append(end_ms - start_ms)
        t_ms = end_ms
    frames.append(blank)
    durations.append(max(int(round(duration * 1000)) - t_ms, 0) + 1000)
    track = work / "subs.apng"
    # disposal=0(그대로), blend=0(덮어쓰기). disposal=1 로 두면 Pillow 가 빈 구간을 앞 프레임에 합쳐
    # 자막이 늦게 사라진다(실측).
    frames[0].save(track, format="PNG", save_all=True, append_images=frames[1:], duration=durations,
                   loop=1, disposal=0, blend=0, default_image=False)
    return track, band_x, band_y


# --- ffmpeg --------------------------------------------------------------

def build_command(tools, req, src, track, out_path, limits):
    track_path, track_x, track_y = track
    w, h = req.output_size
    duration = min(src["duration"], limits.max_input_seconds)
    args = [tools["ffmpeg"], "-hide_banner", "-nostdin", "-v", "warning",
            "-filter_complex_threads", "1",
            "-protocol_whitelist", "file", "-f", src["demuxer"], "-i", "file:" + str(req.video_path),
            "-protocol_whitelist", "file", "-f", "apng", "-i", "file:" + str(track_path)]
    audio_input = None
    if not src["has_audio"]:
        audio_input = 2
        args += ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate={AUDIO_RATE:d}"]

    graph = (f"[0:v]scale=w={w:d}:h={h:d}:force_original_aspect_ratio=increase:flags=bicubic,"
             f"crop={w:d}:{h:d},setsar=1,fps={req.output_fps:d}[base];"
             f"[1:v]format=rgba[subs];"
             f"[base][subs]overlay=x={track_x:d}:y={track_y:d}:eof_action=repeat[mix];"
             f"[mix]format=yuv420p[vout]")
    args += ["-filter_complex", graph, "-map", "[vout]",
             "-map", f"{audio_input:d}:a:0" if audio_input is not None else "0:a:0",
             "-t", f"{duration:.3f}",
             "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-profile:v", "high",
             "-pix_fmt", "yuv420p", "-threads", f"{limits.ffmpeg_threads:d}",
             "-c:a", "aac", "-b:a", "128k", "-ar", f"{AUDIO_RATE:d}", "-ac", "2",
             "-map_metadata", "-1", "-map_chapters", "-1",
             "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
             "-movflags", "+faststart", "-f", "mp4", str(out_path)]
    return args, duration


def verify_output(tools, out_path, req, src_demuxer, overlays, expected_duration, limits, work):
    info = probe(tools["ffprobe"], out_path, "verify", limits.probe_timeout_seconds, demuxer="mov", limits=limits)
    streams = info.get("streams", [])
    v = next((s for s in streams if s.get("codec_type") == "video"), {})
    a = next((s for s in streams if s.get("codec_type") == "audio"), {})
    duration = float(info.get("format", {}).get("duration") or 0)
    w, h = req.output_size
    checks = {
        "container_mp4": "mp4" in info.get("format", {}).get("format_name", ""),
        "video_h264": v.get("codec_name") == "h264",
        "resolution": (v.get("width"), v.get("height")) == (w, h),
        "pix_fmt_yuv420p": v.get("pix_fmt") == "yuv420p",
        "fps": v.get("avg_frame_rate") == f"{req.output_fps}/1",
        "audio_aac": a.get("codec_name") == "aac",
        "duration": abs(duration - expected_duration) <= max(0.15, 2.0 / req.output_fps),
    }
    overlay_checks = []
    for ov in overlays[:5]:
        # 입력 쪽 -ss 는 그 시각 이후 첫 프레임을 준다. 프레임 시각보다 조금 앞을 주어 정확히 그 프레임을 받는다.
        t = max(0.0, (ov["frame"] - 0.2) / req.output_fps)
        frame, base = work / f"verify_{ov['index']:03d}.png", work / f"verify_base_{ov['index']:03d}.png"
        grab = [tools["ffmpeg"], "-hide_banner", "-nostdin", "-v", "error", "-protocol_whitelist", "file",
                "-ss", f"{t:.3f}"]
        run(grab + ["-f", "mov", "-i", "file:" + str(out_path), "-frames:v", "1",
                    "-f", "image2", "-update", "1", str(frame)], "verify", limits.probe_timeout_seconds, limits=limits)
        run(grab + ["-f", src_demuxer, "-i", "file:" + str(req.video_path), "-frames:v", "1",
                    "-vf", f"scale=w={w:d}:h={h:d}:force_original_aspect_ratio=increase:flags=bicubic,crop={w:d}:{h:d}",
                    "-f", "image2", "-update", "1", str(base)], "verify", limits.probe_timeout_seconds, limits=limits)
        overlay_checks.append(_overlay_match(frame, base, ov))
    checks["overlay_visible"] = bool(overlay_checks) and all(c["ok"] for c in overlay_checks)
    return info, checks, overlay_checks


def _pixels(path, mode, box=None):
    """픽셀 튜플 목록. getdata() 는 Pillow 12 에서 폐기 예정이라 tobytes() 로 읽는다(11·12 공통)."""
    with Image.open(path) as im:
        im = im.convert(mode)
        if box:
            im = im.crop(box)
        data, n = im.tobytes(), len(mode)
    return [tuple(data[i:i + n]) for i in range(0, len(data), n)]


def _overlay_match(frame_path, base_path, ov):
    """자막이 실제로 그려졌는지.

    자막 PNG 의 완전 불투명 픽셀(글자 + 테두리)을 출력 프레임과 원본 프레임(같은 시점, 같은 크기 변환)에서
    읽는다. 자막이 그려졌다면 출력은 원본보다 자막 색에 가까워야 한다.
    작은 글자는 픽셀 대부분이 가장자리라 압축과 색 서브샘플링으로 색이 번진다. 그래서 절대 오차가 아니라
    "원본보다 가까운 픽셀 비율"과 "원본 대비 중앙값 오차"로 판정한다.
    """
    box = (ov["x"], ov["y"], ov["x"] + ov["w"], ov["y"] + ov["h"])
    cue = _pixels(ov["path"], "RGBA")
    out = _pixels(frame_path, "RGB", box)
    base = _pixels(base_path, "RGB", box)
    d_out, d_base = [], []
    for (r, g, b, a), o, s in zip(cue, out, base):
        if a == 255:
            d_out.append((abs(o[0] - r) + abs(o[1] - g) + abs(o[2] - b)) / 3)
            d_base.append((abs(s[0] - r) + abs(s[1] - g) + abs(s[2] - b)) / 3)
    n = len(d_out)
    if n == 0:
        return {"cue": ov["index"], "opaque_pixels": 0, "ok": False}
    m_out, m_base = statistics.median(d_out), statistics.median(d_base)
    closer = sum(1 for a, b in zip(d_out, d_base) if a < b) / n
    # 자막이 없으면 출력은 원본과 거의 같으므로 closer 는 0.5 이하, m_out 은 m_base 와 비슷하다.
    # 자막이 있어도 원본 배경이 우연히 자막색인 픽셀(검은 배경 위 검은 테두리 등)은 closer 에 들어가지 않는다.
    return {"cue": ov["index"], "opaque_pixels": n, "median_diff_output": round(m_out, 2),
            "median_diff_source": round(m_base, 2), "closer_to_subtitle_ratio": round(closer, 4),
            "ok": n >= 50 and closer >= 0.65 and m_out <= 0.5 * m_base}


# --- 진입점 -------------------------------------------------------------

def compose(raw_request, roots, out_dir, env_label, limits=Limits()):
    """결과 dict 를 돌려준다. 예외를 밖으로 던지지 않는다. state 는 ASSET_READY 또는 FAILED."""
    started, t0 = _utc(), time.monotonic()
    out_dir = Path(out_dir).resolve()
    result = {
        "contract": CONTRACT,
        "engine": {"id": ENGINE_ID, "version": ENGINE_VERSION, **_engine_commit()},
        "job_id": raw_request.get("job_id") if isinstance(raw_request, dict) else None,
        "state": "FAILED",
        "environment": {"label": env_label or "UNLABELED", "python": platform.python_version(),
                        "platform": platform.platform(), "pillow": PIL.__version__},
        "started_at": started,
    }
    work = None
    try:
        tools = check_toolchain()
        result["environment"]["ffmpeg"] = tools["ffmpeg_version"]
        req = parse_request(raw_request, roots, limits)
        result["request_sha256"] = req.canonical_sha256()
        final_dir = out_dir / req.job_id
        if final_dir.exists():
            raise ComposeError("JOB_EXISTS", "같은 job_id 의 결과가 이미 있습니다. 덮어쓰지 않습니다.", "commit",
                               {"path": str(final_dir)})
        out_dir.mkdir(parents=True, exist_ok=True)
        work = Path(tempfile.mkdtemp(prefix=f".{req.job_id}.", dir=out_dir))

        src = inspect_input(tools["ffprobe"], req.video_path, limits)
        result["input"] = {"uri": req.video_path.as_uri(), "sha256": sha256_file(req.video_path),
                           "bytes": req.video_path.stat().st_size,
                           **{k: src[k] for k in ("demuxer", "width", "height", "duration",
                                                  "video_codec", "audio_codec", "has_audio")}}
        cues, cues_sha = load_cues(req.subtitles_source, roots, limits, src["duration"])
        result["subtitles"] = {"count": len(cues), "sha256": cues_sha}
        result["font"] = {"uri": req.font.path.as_uri(), "sha256": req.font.sha256, "license": req.font.license,
                          "license_uri": req.font.license_path.as_uri()}

        overlays, layout = rasterize(cues, req.font.path, req.output_size, req.safe_area, req.style, limits, work,
                                     req.output_fps)
        result["layout"] = layout

        out_path = work / "output.mp4"
        track = write_track(overlays, src["duration"], work)
        args, expected = build_command(tools, req, src, track, out_path, limits)
        rendered = run(args, "render", limits.timeout_seconds, limits=limits)
        result["render"] = {"argv": args, "elapsed_seconds": rendered["elapsed_seconds"], "stderr": rendered["stderr"],
                            "x264_threads": limits.ffmpeg_threads,
                            "deterministic_mode": limits.ffmpeg_threads == 1}

        info, checks, overlay_checks = verify_output(tools, out_path, req, src["demuxer"], overlays, expected, limits, work)
        result["checks"], result["overlay_checks"] = checks, overlay_checks
        (work / "output.ffprobe.json").write_text(json.dumps(info, ensure_ascii=False, indent=2))
        if not all(checks.values()):
            raise ComposeError("VERIFY_FAILED", "출력 검사에 실패했습니다.", "verify",
                               {"failed": [k for k, ok in checks.items() if not ok]})

        for pattern in ("cue_*.png", "verify_*.png", "subs.apng"):
            for p in work.glob(pattern):
                p.unlink()
        result["output"] = {"file": "output.mp4", "sha256": sha256_file(out_path), "bytes": out_path.stat().st_size,
                            "ffprobe_file": "output.ffprobe.json",
                            "width": req.output_size[0], "height": req.output_size[1], "fps": req.output_fps,
                            "duration": float(info["format"]["duration"])}
        result["state"] = "ASSET_READY"
        result["finished_at"], result["elapsed_seconds"] = _utc(), round(time.monotonic() - t0, 3)
        (work / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
        os.rename(work, final_dir)
        work = None
        result["output"]["uri"] = (final_dir / "output.mp4").as_uri()
        return result
    except ComposeError as exc:
        result["error"] = exc.to_dict()
    except Exception as exc:  # 예상 못 한 오류도 결과 JSON 으로 돌려준다.
        result["error"] = {"code": "INTERNAL", "message": type(exc).__name__, "stage": "internal",
                           "detail": {"repr": repr(exc)[:500]}}
    finally:
        if work is not None:
            shutil.rmtree(work, ignore_errors=True)
    result["finished_at"], result["elapsed_seconds"] = _utc(), round(time.monotonic() - t0, 3)
    _write_failure(out_dir, result)
    return result


def _write_failure(out_dir, result):
    try:
        failed = out_dir / "_failed"
        failed.mkdir(parents=True, exist_ok=True)
        job = result.get("job_id") if isinstance(result.get("job_id"), str) else "invalid"
        safe = "".join(ch if ch.isalnum() or ch in "-_." else "_" for ch in job)[:96].lstrip(".") or "invalid"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        (failed / f"{safe}.{stamp}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    except OSError:
        pass
