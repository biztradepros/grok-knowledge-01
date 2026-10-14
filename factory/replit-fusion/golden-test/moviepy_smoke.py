"""DF-GT-VIDEO-001: MoviePy 최소 실행 시험.

합성 원본만 쓴다. 외부 영상, 유료 API, 네트워크를 쓰지 않는다.

1. 16:9 원본(1280x720, 6초, 사인파 오디오, 2~3초 무음 구간)을 만든다.
2. 원본을 재활용해 9:16 쇼츠(540x960)로 자르고 이어 붙인다.
3. 한국어 자막을 얹고 H.264/AAC mp4로 내보낸다.
4. ffprobe 로 해상도, 길이, 코덱을 읽어 evidence JSON 을 남긴다.

usage: python moviepy_smoke.py OUT_DIR [FONT_PATH]
"""

import hashlib
import json
import subprocess
import sys
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
from moviepy import (
    AudioClip,
    ColorClip,
    CompositeVideoClip,
    TextClip,
    VideoClip,
    concatenate_videoclips,
)
import moviepy

OUT = Path(sys.argv[1])
FONT = sys.argv[2] if len(sys.argv) > 2 else "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 24


def source_frame(t):
    # 움직이는 사각형이 있는 그라데이션. 프레임마다 내용이 달라야 편집 결과를 확인할 수 있다.
    h, w = 720, 1280
    frame = np.zeros((h, w, 3), dtype=np.uint8)
    frame[:, :, 0] = np.linspace(30, 200, w, dtype=np.uint8)[None, :]
    frame[:, :, 2] = int(80 + 25 * t)
    x = int((w - 200) * (t / 6.0))
    frame[260:460, x : x + 200] = (255, 220, 0)
    return frame


def source_audio(t):
    t = np.asarray(t)
    tone = 0.3 * np.sin(2 * np.pi * 440 * t)
    silent = (t >= 2.0) & (t < 3.0)
    return np.where(silent, 0.0, tone)[..., None].repeat(2, axis=-1)


started = time.time()
src = VideoClip(source_frame, duration=6).with_fps(FPS)
src = src.with_audio(AudioClip(source_audio, duration=6, fps=44100))
src_path = OUT / "source_16x9.mp4"
src.write_videofile(str(src_path), codec="libx264", audio_codec="aac", logger=None)

# 원본 재활용: 무음 구간(2~3초)을 빼고 두 구간을 잇는다.
cut = concatenate_videoclips([src.subclipped(0, 2), src.subclipped(3, 6)])

# 9:16 쇼츠: 가운데를 405x720 으로 자르고 540x960 으로 키운다.
short = cut.cropped(x_center=640, width=405, height=720).resized((540, 960))

title = (
    TextClip(font=FONT, text="DREAM 부품 시험", font_size=44, color="white",
             bg_color="black", margin=(16, 10))
    .with_duration(1.5)
    .with_position(("center", 80))
)
sub = (
    TextClip(font=FONT, text="자막 자동 합성 확인", font_size=36, color="yellow",
             stroke_color="black", stroke_width=2, margin=(10, 10))
    .with_start(1.5)
    .with_duration(short.duration - 1.5)
    .with_position(("center", 820))
)
bar = ColorClip((540, 12), color=(255, 0, 80)).with_duration(short.duration).with_position((0, 0))

final = CompositeVideoClip([short, bar, title, sub], size=(540, 960))
out_path = OUT / "short_9x16.mp4"
final.write_videofile(str(out_path), codec="libx264", audio_codec="aac", fps=FPS, logger=None)
final.save_frame(str(OUT / "short_frame_t2.png"), t=2.0)
elapsed = round(time.time() - started, 2)


def probe(path):
    raw = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration:stream=codec_type,codec_name,width,height",
         "-of", "json", str(path)],
        capture_output=True, text=True, check=True,
    ).stdout
    return json.loads(raw)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


src_p, out_p = probe(src_path), probe(out_path)
video = next(s for s in out_p["streams"] if s["codec_type"] == "video")
audio = [s for s in out_p["streams"] if s["codec_type"] == "audio"]
duration = float(out_p["format"]["duration"])

checks = {
    "resolution_540x960": (video["width"], video["height"]) == (540, 960),
    "video_h264": video["codec_name"] == "h264",
    "audio_aac_present": bool(audio) and audio[0]["codec_name"] == "aac",
    "silence_removed_duration_about_5s": abs(duration - 5.0) < 0.2,
}
evidence = {
    "test_id": "DF-GT-VIDEO-001",
    "part_id": "DF-PART-VID-001",
    "tool": "moviepy",
    "tool_version": version("moviepy"),
    # moviepy 2.2.1 패키지의 moviepy.__version__ 은 2.1.2 로 남아 있다. 설치 메타데이터를 정본으로 쓴다.
    "module_version_attr": moviepy.__version__,
    "font": FONT,
    "elapsed_seconds": elapsed,
    "source": {"file": src_path.name, "sha256": sha256(src_path), "ffprobe": src_p},
    "output": {"file": out_path.name, "sha256": sha256(out_path), "ffprobe": out_p},
    "frame": {"file": "short_frame_t2.png", "sha256": sha256(OUT / "short_frame_t2.png")},
    "checks": checks,
    "result": "PASS" if all(checks.values()) else "FAIL",
}
(OUT / "DF-GT-VIDEO-001.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
print(json.dumps({"result": evidence["result"], "checks": checks, "elapsed": elapsed}, ensure_ascii=False))
