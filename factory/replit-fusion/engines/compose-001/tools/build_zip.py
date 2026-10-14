"""소스 ZIP. 파일 순서와 시각을 고정해 같은 소스면 같은 해시가 나온다.

usage: python tools/build_zip.py OUT.zip
"""

import hashlib
import sys
import zipfile
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1]
FIXED_TIME = (2026, 10, 14, 0, 0, 0)


def files():
    for p in sorted(ENGINE.rglob("*")):
        rel = p.relative_to(ENGINE)
        if p.is_file() and "__pycache__" not in rel.parts and p.suffix not in (".zip", ".pyc"):
            yield p, rel


def build(out):
    with zipfile.ZipFile(out, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p, rel in files():
            info = zipfile.ZipInfo(f"compose-001/{rel.as_posix()}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o644 << 16)
            z.writestr(info, p.read_bytes())
    return hashlib.sha256(Path(out).read_bytes()).hexdigest()


if __name__ == "__main__":
    print(build(sys.argv[1]))
