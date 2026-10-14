"""결정론적 입력 영상: 1280x720 30fps 6초, 440Hz 사인파, 2~3초 무음. H.264/AAC MP4.

외부 파일을 쓰지 않는다. ffmpeg 의 lavfi 시험 신호만 쓴다.
같은 ffmpeg 빌드에서는 같은 해시가 나와야 한다 (bitexact, 스레드 1).

usage: python fixtures/make_fixture.py OUT.mp4
"""

import hashlib
import shutil
import subprocess
import sys


def make(out):
    ffmpeg = shutil.which("ffmpeg")
    subprocess.run(
        [ffmpeg, "-hide_banner", "-nostdin", "-v", "error", "-y",
         "-f", "lavfi", "-i", "testsrc2=size=1280x720:rate=30:duration=6",
         "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=48000:duration=6",
         "-filter_complex", "[1:a]volume=enable='between(t,2,3)':volume=0[a]",
         "-map", "0:v", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p", "-threads", "1",
         "-c:a", "aac", "-b:a", "128k", "-ac", "2",
         "-map_metadata", "-1", "-fflags", "+bitexact", "-flags:v", "+bitexact", "-flags:a", "+bitexact",
         "-f", "mp4", out],
        check=True, timeout=120,
    )
    return hashlib.sha256(open(out, "rb").read()).hexdigest()


if __name__ == "__main__":
    print(make(sys.argv[1]))
