"""같은 요청을 N번 렌더해 출력 해시가 같은지, 자막이 많을 때 자원을 얼마나 쓰는지 잰다.

usage: python tools/repeat_run.py --env-label LABEL --runs 20 [--stress] OUT.json
"""

import argparse
import collections
import json
import resource
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))
sys.path.insert(0, str(ENGINE / "fixtures"))
sys.path.insert(0, str(ENGINE / "tools"))

import make_fixture  # noqa: E402
from golden_run import request  # noqa: E402
from df_compose import compose  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-label", required=True)
    ap.add_argument("--runs", type=int, default=20)
    ap.add_argument("--stress", action="store_true", help="자막 200개, 60fps")
    ap.add_argument("out")
    a = ap.parse_args()
    tmp = Path(tempfile.mkdtemp(prefix="dfc-repeat-"))
    try:
        video = tmp / "fixture.mp4"
        fixture_sha = make_fixture.make(str(video))
        roots = [str(tmp), str(ENGINE / "assets"), str(ENGINE / "fixtures")]
        if a.stress:
            subs = [{"start": round(i * 0.03, 3), "end": round(i * 0.03 + 0.025, 3), "text": f"자막 {i:03d}번"}
                    for i in range(200)]
        else:
            subs = {"format": "srt", "uri": (ENGINE / "fixtures" / "subtitles_ko.srt").as_uri()}
        hashes, secs, states, errors = collections.Counter(), [], collections.Counter(), []
        started = time.time()
        for i in range(a.runs):
            req = request(f"DF-JOB-REPEAT-{i:03d}", video, subs)
            if a.stress:
                req["output_fps"] = 60
            r = compose(req, roots, tmp / "out", a.env_label)
            states[r["state"]] += 1
            if r["state"] != "ASSET_READY":
                errors.append(r["error"])
                continue
            hashes[r["output"]["sha256"]] += 1
            secs.append(r["render"]["elapsed_seconds"])
            shutil.rmtree(tmp / "out" / req["job_id"])
        summary = {
            "test_id": "DF-GT-COMPOSE-STRESS" if a.stress else "DF-GT-COMPOSE-REPEAT",
            "environment_label": a.env_label,
            "runs": a.runs,
            "mode": "200 cues, 1080x1920, 60fps" if a.stress else "3 cues (SRT), 1080x1920, 30fps",
            "fixture_sha256": fixture_sha,
            "states": dict(states),
            "distinct_output_sha256": dict(hashes),
            "deterministic": len(hashes) == 1 and states.get("ASSET_READY") == a.runs,
            "render_seconds": {"min": min(secs), "median": statistics.median(secs), "max": max(secs)} if secs else None,
            "wall_seconds": round(time.time() - started, 1),
            "max_rss_mb": {"ffmpeg_children": resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss // 1024,
                           "python": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss // 1024},
            "errors": errors[:5],
        }
        Path(a.out).write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({k: summary[k] for k in ("states", "deterministic", "render_seconds", "max_rss_mb")},
                         ensure_ascii=False))
        return 0 if summary["deterministic"] else 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
