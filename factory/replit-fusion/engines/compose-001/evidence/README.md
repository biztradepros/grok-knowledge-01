# Evidence — DF-ENGINE-COMPOSE-001

환경 라벨: **SANDBOX/claude-code-remote-container (NOT Replit)**. Replit 실행 증거는 없다.

| 파일 | 증명하는 것 |
|---|---|
| `prior_evidence_check.json` | 이전 MoviePy 증거의 해시 재검증, `__version__` 불일치 원인(상류 태그) |
| `env_manifest.json` | 파이썬, Pillow, ffmpeg 버전과 빌드 설정, 엔진 소스 파일별 sha256 |
| `tests_py313-pillow12.log` | 시험 44개 통과 (Python 3.13.16, Pillow 12.3.0) |
| `tests_py313-pillow11.log` | 시험 44개 통과 (Python 3.13.16, Pillow 11.3.0) |
| `tests_py311-pillow11.log` | 시험 44개 통과 (Python 3.11.17, Pillow 11.3.0) |
| `golden/golden_summary.json` | GOLDEN RUN PASS. SRT 입력과 JSON 입력이 같은 출력 해시 |
| `golden/result_A_srt.json` | 결과 JSON 전체. 엔진 커밋 `bd4713c`, dirty false, 검사 8개, 자막 표시 검사 수치 |
| `golden/output_golden_A.mp4` | 실제 출력 1080x1920 30fps H.264/AAC 6초, sha256 `1494ea90c3b5…` |
| `golden/output.ffprobe.json` | 출력 ffprobe |
| `golden/frame_t*.png` | 1.0초, 2.7초, 4.7초 프레임 (360x640 축소) |
| `repeat_20.json` | 같은 요청 20회, 출력 해시 1종 |
| `stress_200cues.json` | 자막 200개 60fps 3회, 해시 1종, 렌더 8.2초, ffmpeg 최대 RSS 319MB |
| `determinism_investigation.json` | 간헐 해시 불일치의 원인 추적 기록 |

결과 JSON 의 경로는 이 세션 scratchpad 의 절대 경로다.

## 소스 ZIP 독립 실행

`tools/build_zip.py` 로 만든 ZIP(파일 45개)을 빈 폴더에 풀어 저장소 없이 돌렸다.

- Python 3.11.17 + Pillow 11.3.0: 시험 44개 OK
- `golden_run.py`: PASS, 출력 sha256 `1494ea90c3b5…` — Python 3.13 + Pillow 12.3 환경의 값과 같다
- git 밖이라 결과 JSON 의 `engine.git_commit` 은 null 이다. 이때 출처는 ZIP sha256 으로 대신한다

ZIP 은 같은 소스면 같은 해시가 나오도록 파일 순서와 시각을 고정한다. 커밋하지 않는다. 다시 만들려면 `python tools/build_zip.py OUT.zip`.
