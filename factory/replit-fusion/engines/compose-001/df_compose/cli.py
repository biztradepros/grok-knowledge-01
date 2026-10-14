"""python -m df_compose --request job.json --allow-root DIR --out-dir DIR --env-label LABEL

종료 코드: 0 = ASSET_READY, 2 = FAILED, 64 = 사용법 오류.
결과 JSON 은 표준 출력으로 한 번 나간다.
"""

import argparse
import json
import os
import sys

from .contract import Limits
from .render import compose


def main(argv=None):
    p = argparse.ArgumentParser(prog="df_compose", description="DF-ENGINE-COMPOSE-001")
    p.add_argument("--request", required=True, help="요청 JSON 파일, '-' 이면 표준 입력")
    p.add_argument("--allow-root", action="append", default=[],
                   help="입력 파일이 있어야 하는 폴더. 여러 번 줄 수 있다. DF_COMPOSE_ALLOWED_ROOTS 도 읽는다.")
    p.add_argument("--out-dir", required=True)
    p.add_argument("--env-label", default=os.environ.get("DF_ENV_LABEL"),
                   help="실행 환경 표시. 예: 'SANDBOX/claude-code-remote', 'REPLIT/<repl-id>'")
    p.add_argument("--timeout", type=float, default=None, help="렌더 시간 한도(초)")
    args = p.parse_args(argv)

    roots = list(args.allow_root)
    roots += [r for r in os.environ.get("DF_COMPOSE_ALLOWED_ROOTS", "").split(os.pathsep) if r]
    if not roots:
        print("--allow-root 또는 DF_COMPOSE_ALLOWED_ROOTS 가 필요합니다.", file=sys.stderr)
        return 64
    try:
        if args.request == "-":
            raw = json.load(sys.stdin)
        else:
            with open(args.request, encoding="utf-8") as f:
                raw = json.load(f)
    except (OSError, ValueError) as exc:
        print(f"요청 JSON 을 읽을 수 없습니다: {exc}", file=sys.stderr)
        return 64

    limits = Limits() if args.timeout is None else Limits(timeout_seconds=args.timeout)
    result = compose(raw, roots, args.out_dir, args.env_label, limits)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["state"] == "ASSET_READY" else 2


if __name__ == "__main__":
    sys.exit(main())
