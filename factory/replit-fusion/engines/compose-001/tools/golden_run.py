"""GOLDEN RUN: 결정론적 입력 → 1080x1920 한국어 자막 쇼츠. 두 번 렌더해서 해시를 비교한다.

Replit 이나 다른 환경에서도 같은 명령으로 돌리고, 결과의 env label 과 해시를 비교한다.

usage: python tools/golden_run.py --env-label LABEL OUT_DIR
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(ENGINE / "fixtures"))

import make_fixture  # noqa: E402
from df_compose import compose  # noqa: E402

FONTS = json.loads((ENGINE / "assets" / "fonts" / "fonts.json").read_text())["fonts"][0]


def request(job_id, video, subtitles):
    return {
        "contract": "df.compose.v1",
        "job_id": job_id,
        "video_uri": video.as_uri(),
        "subtitles_json_or_srt": subtitles,
        "output_size": [1080, 1920],
        "output_fps": 30,
        "safe_area": {"top": 0.10, "bottom": 0.18, "left": 0.06, "right": 0.06},
        "font_asset": {
            "uri": (ENGINE / "assets" / "fonts" / FONTS["file"]).as_uri(),
            "sha256": FONTS["sha256"],
            "license": FONTS["license"],
            "license_uri": (ENGINE / "assets" / "fonts" / FONTS["license_file"]).as_uri(),
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-label", required=True)
    ap.add_argument("out_dir")
    a = ap.parse_args()
    out = Path(a.out_dir).resolve()
    if out.exists():
        sys.exit(f"{out} 가 이미 있습니다. 새 폴더를 주세요.")
    inputs = out / "inputs"
    inputs.mkdir(parents=True)
    video = inputs / "fixture.mp4"
    fixture_sha = make_fixture.make(str(video))
    roots = [str(inputs), str(ENGINE / "assets"), str(ENGINE / "fixtures")]

    srt = {"format": "srt", "uri": (ENGINE / "fixtures" / "subtitles_ko.srt").as_uri()}
    cues = json.loads((ENGINE / "fixtures" / "subtitles_ko.json").read_text(encoding="utf-8"))
    runs = {
        "A_srt": compose(request("DF-JOB-COMPOSE-GOLDEN-A", video, srt), roots, out / "jobs", a.env_label),
        "B_json": compose(request("DF-JOB-COMPOSE-GOLDEN-B", video, cues), roots, out / "jobs", a.env_label),
    }
    for name, r in runs.items():
        (out / f"result_{name}.json").write_text(json.dumps(r, ensure_ascii=False, indent=2))

    a_res, b_res = runs["A_srt"], runs["B_json"]
    frames = []
    if a_res["state"] == "ASSET_READY":
        job_dir = out / "jobs" / "DF-JOB-COMPOSE-GOLDEN-A"
        shutil.copyfile(job_dir / "output.ffprobe.json", out / "output.ffprobe.json")
        for t in (1.0, 2.7, 4.7):
            frame = out / f"frame_t{t:.1f}.png"
            subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", "-v", "error", "-ss", f"{t:.1f}",
                            "-i", str(job_dir / "output.mp4"), "-frames:v", "1", "-vf", "scale=360:640",
                            str(frame)], check=True, timeout=60)
            frames.append(frame.name)

    summary = {
        "test_id": "DF-GT-COMPOSE-001",
        "environment_label": a.env_label,
        "fixture_sha256": fixture_sha,
        "states": {k: v["state"] for k, v in runs.items()},
        "errors": {k: v.get("error") for k, v in runs.items() if v.get("error")},
        "output_sha256": {k: v.get("output", {}).get("sha256") for k, v in runs.items()},
        "subtitles_sha256": {k: v.get("subtitles", {}).get("sha256") for k, v in runs.items()},
        "deterministic_output": a_res.get("output", {}).get("sha256") is not None
        and a_res["output"]["sha256"] == b_res.get("output", {}).get("sha256"),
        "checks": a_res.get("checks"),
        "overlay_checks": a_res.get("overlay_checks"),
        "render_seconds": {k: v.get("render", {}).get("elapsed_seconds") for k, v in runs.items()},
        "frames": frames,
    }
    summary["result"] = "PASS" if all(s == "ASSET_READY" for s in summary["states"].values()) \
        and summary["deterministic_output"] and all(a_res["checks"].values()) else "FAIL"
    (out / "golden_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(json.dumps({k: summary[k] for k in ("result", "states", "deterministic_output", "output_sha256")},
                     ensure_ascii=False, indent=2))
    return 0 if summary["result"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
