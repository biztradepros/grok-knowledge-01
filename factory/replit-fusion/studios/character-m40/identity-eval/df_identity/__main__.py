"""python -m df_identity --models DIR --master A.png [--master B.png] --candidate C.png ... \
       [--protected SOPHIE=S1.png,S2.png] [--out result.json]

종료 코드: 0 = 실행 완료(후보별 판정은 결과에), 2 = MASTER/모델 오류, 64 = 사용법 오류.
"""

import argparse
import json
import sys

from .evaluate import EvalError, Evaluator


def main(argv=None):
    ap = argparse.ArgumentParser(prog="df_identity")
    ap.add_argument("--models", required=True)
    ap.add_argument("--master", action="append", required=True)
    ap.add_argument("--candidate", action="append", required=True)
    ap.add_argument("--protected", action="append", default=[], help="NAME=a.png,b.png")
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    protected = {}
    for spec in a.protected:
        if "=" not in spec:
            print("--protected 는 NAME=a.png,b.png 형식입니다.", file=sys.stderr)
            return 64
        name, files = spec.split("=", 1)
        protected[name] = [f for f in files.split(",") if f]
    try:
        result = Evaluator(a.models).evaluate(a.master, a.candidate, protected)
    except EvalError as exc:
        print(json.dumps({"error": exc.to_dict()}, ensure_ascii=False, indent=2))
        return 2
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(text + "\n")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
