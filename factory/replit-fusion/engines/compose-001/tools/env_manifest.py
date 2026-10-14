"""실행 환경 기록. usage: python tools/env_manifest.py --env-label LABEL [OUT.json]"""

import argparse
import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ENGINE))

import PIL  # noqa: E402

from df_compose import CONTRACT, ENGINE_ID, ENGINE_VERSION  # noqa: E402
from df_compose.media import check_toolchain  # noqa: E402


def sh(*args):
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def source_hashes():
    out = {}
    for p in sorted(ENGINE.rglob("*")):
        if p.is_file() and "__pycache__" not in p.parts and "evidence" not in p.parts and p.suffix != ".zip":
            out[str(p.relative_to(ENGINE))] = hashlib.sha256(p.read_bytes()).hexdigest()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--env-label", required=True)
    ap.add_argument("out", nargs="?")
    a = ap.parse_args()
    tools = check_toolchain()
    manifest = {
        "engine": {"id": ENGINE_ID, "version": ENGINE_VERSION, "contract": CONTRACT},
        "environment_label": a.env_label,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "python": sys.version.split()[0],
        "python_executable_is_venv": sys.prefix != sys.base_prefix,
        "pillow": PIL.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "cpu_count": __import__("os").cpu_count(),
        "ffmpeg": tools["ffmpeg_version"],
        "ffmpeg_path": tools["ffmpeg"],
        "ffprobe_path": tools["ffprobe"],
        "required_encoders": tools["encoders"],
        "required_filters": tools["filters"],
        "ffmpeg_configuration": sh(tools["ffmpeg"], "-hide_banner", "-buildconf"),
        "git_commit": sh("git", "-C", str(ENGINE), "rev-parse", "HEAD"),
        "git_dirty": bool(sh("git", "-C", str(ENGINE), "status", "--porcelain", "--", ".")),
        "source_sha256": source_hashes(),
    }
    text = json.dumps(manifest, ensure_ascii=False, indent=2)
    if a.out:
        Path(a.out).write_text(text + "\n")
    else:
        print(text)


if __name__ == "__main__":
    main()
