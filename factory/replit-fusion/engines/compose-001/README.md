---
engine: DF-ENGINE-COMPOSE-001
parent: DF-MULTILAB-ENGINE-FUSION-20261014-001
contract: df.compose.v1
version: 0.1.0
status: draft
execution: SANDBOX PASS (claude-code-remote container) / REPLIT HOLD
---

# DF-ENGINE-COMPOSE-001 — 영상 합성 엔진

영상 하나와 자막 목록 하나, 글꼴 하나를 받아 9:16(또는 지정 크기) H.264/AAC MP4 와 ffprobe JSON, 결과 JSON 을 낸다.

공장 전체가 아니라 부품 하나다. FM 3.0, FM v2, FM v3 코드는 건드리지 않는다.

## 빠르게 돌리기

필요한 것: Python 3.11 이상, Pillow 11 이상, `ffmpeg`/`ffprobe` (libx264, aac 인코더 포함).

```
pip install -r requirements.txt
python -m unittest discover -s tests -t tests          # 44개 시험
python tools/golden_run.py --env-label "LOCAL/내-PC" /tmp/golden
```

CLI:

```
python -m df_compose --request job.json \
  --allow-root /data/in --allow-root ./assets \
  --out-dir /data/out --env-label "REPLIT/<repl-id>"
```

종료 코드 0 = `ASSET_READY`, 2 = `FAILED`, 64 = 사용법 오류. 결과 JSON 은 표준 출력과 `<out>/<job_id>/result.json` 에 같이 나온다.

라이브러리:

```python
from df_compose import compose
result = compose(request_dict, roots=["/data/in", "./assets"], out_dir="/data/out", env_label="REPLIT/abc")
```

`compose` 는 예외를 던지지 않는다. 항상 결과 dict 를 돌려준다.

## 요청 계약 df.compose.v1

```json
{
  "contract": "df.compose.v1",
  "job_id": "DF-JOB-COMPOSE-20261014-001",
  "video_uri": "file:///data/in/source.mp4",
  "subtitles_json_or_srt": {"format": "srt", "uri": "file:///data/in/subs.srt"},
  "output_size": [1080, 1920],
  "output_fps": 30,
  "safe_area": {"top": 0.10, "bottom": 0.18, "left": 0.06, "right": 0.06},
  "font_asset": {
    "uri": "file:///app/assets/fonts/NanumGothic-Regular.ttf",
    "sha256": "76f45ef4a6bcff344c837c95a7dcc26e017e38b5846d5ae0cdcb5b86be2e2d31",
    "license": "OFL-1.1",
    "license_uri": "file:///app/assets/fonts/OFL.txt"
  },
  "style": {"font_size_ratio": 0.045, "fill": "#FFFFFF", "stroke": "#000000", "stroke_ratio": 0.08, "line_spacing": 1.25}
}
```

| 필드 | 규칙 |
|---|---|
| `job_id` | `[A-Za-z0-9][A-Za-z0-9_.-]{2,95}`, `..` 금지. 결과 폴더 이름이 된다. 이미 있으면 덮어쓰지 않는다 |
| `video_uri` | `file://` 또는 경로만. 허용 루트 안의 일반 파일. MP4/MOV 또는 MKV/WebM 머리 바이트 |
| `subtitles_json_or_srt` | `[{"start","end","text"}]` 목록, 또는 `{"format":"srt"|"json","text":…}`, 또는 `{"format":…,"uri":…}` |
| `output_size` | 128~2160 짝수 |
| `output_fps` | 12~60 정수 |
| `safe_area` | 네 변 비율 0~0.45. 자막은 안전 영역 아래쪽 가운데에 붙는다 |
| `font_asset` | sha256 일치, 라이선스는 OFL-1.1 / Apache-2.0 / MIT / UFL-1.0, 라이선스 파일 필수 |
| `style` | 선택. 위 다섯 키만 |

자막 규칙: 200개, 한 개 200자, 3줄, 시간 겹침 금지, 프레임 하나 이상 덮어야 함. 끝 시각은 영상 길이로 자른다.

## 결과 JSON

`state` 는 `ASSET_READY` 또는 `FAILED` 다. FM v2 상태 계약의 `ASSET_READY` 와 같은 뜻이다. 그다음 `REVIEW_REQUIRED → APPROVED` 는 호출하는 쪽(FM 라우터와 Human Gate)이 한다.

주요 필드: `engine`(id, version, git_commit, dirty), `environment`(label, python, pillow, ffmpeg), `request_sha256`, `input`(sha256, 코덱, 길이), `subtitles`(count, sha256), `font`(sha256, license), `render`(argv, stderr, x264_threads, deterministic_mode), `checks`, `overlay_checks`, `output`(sha256, bytes, uri), `error`(code, message, stage, detail).

출력 폴더:

```
<out>/<job_id>/output.mp4
<out>/<job_id>/output.ffprobe.json
<out>/<job_id>/result.json
<out>/_failed/<job_id>.<UTC>.json      실패한 경우만
```

### 검사 (`checks`)

컨테이너 mp4, H.264, 해상도, yuv420p, fps, AAC, 길이(±0.15초), 자막 표시. 하나라도 false 면 `VERIFY_FAILED` 이고 출력은 남지 않는다.

자막 표시 검사는 앞 5개 자막마다 실제로 걸리는 출력 프레임을 꺼내, 자막 PNG 의 불투명 픽셀이 원본 프레임보다 자막 색에 가까운지 본다.

### 오류 코드

| stage | code |
|---|---|
| environment | `TOOL_MISSING`, `CODEC_UNAVAILABLE` |
| validate | `BAD_REQUEST`, `UNKNOWN_FIELD`, `CONTRACT_MISMATCH`, `BAD_JOB_ID`, `BAD_URI`, `SCHEME_NOT_ALLOWED`, `NO_ALLOWED_ROOTS`, `PATH_OUTSIDE_ROOTS`, `NOT_FOUND`, `NOT_REGULAR_FILE`, `EMPTY_FILE`, `FILE_TOO_LARGE`, `BAD_FIELD`, `BAD_FONT`, `FONT_LICENSE_NOT_ALLOWED`, `FONT_HASH_MISMATCH`, `BAD_SUBTITLES` |
| probe_input | `CONTAINER_NOT_ALLOWED`, `NO_VIDEO_STREAM`, `VIDEO_CODEC_NOT_ALLOWED`, `AUDIO_CODEC_NOT_ALLOWED`, `BAD_DIMENSIONS`, `BAD_DURATION`, `PROBE_UNREADABLE` |
| subtitles | `BAD_SUBTITLES`, `BAD_SRT`, `TOO_MANY_CUES`, `CUE_OVERLAP`, `CUE_AFTER_END` |
| rasterize | `SAFE_AREA_TOO_SMALL`, `FONT_UNREADABLE`, `GLYPH_MISSING`, `CUE_TOO_LONG_FOR_AREA`, `CUE_SHORTER_THAN_FRAME` |
| render / verify | `TIMEOUT`, `PROCESS_FAILED`, `CPU_LIMIT`, `OUTPUT_SIZE_LIMIT`, `KILLED`, `SIGNALED`, `VERIFY_FAILED` |
| commit | `JOB_EXISTS` |
| internal | `INTERNAL` |

## 구조

```
validate → probe_input → subtitles → rasterize → write_track → render → verify → commit
```

- 자막 글자는 Pillow 로 PNG 로 그린다. ffmpeg 필터 문자열에는 사용자 문자열이 들어가지 않는다.
- 자막 전체를 APNG 하나로 묶는다. 입력은 원본과 자막 트랙 두 개뿐이다.
- x264 는 기본 1스레드다. 같은 ffmpeg 빌드에서 같은 요청은 같은 해시를 낸다.
- 리눅스에서는 ffmpeg 에 `RLIMIT_AS`, `RLIMIT_CPU`, `RLIMIT_FSIZE` 를 건다.

자세한 공격 검토는 [REDTEAM.md](REDTEAM.md).

## 글꼴

`assets/fonts/NanumGothic-Regular.ttf` — 나눔고딕, SIL OFL 1.1, `google/fonts` 커밋 `66928797f271…` 에서 받음. 출처와 해시는 `assets/fonts/fonts.json`. OFL 은 앱에 넣어 배포하고 상업적으로 쓸 수 있다. 글꼴 파일만 따로 팔 수는 없다.

## Replit 연동 메모

아직 Replit 에서 실행하지 않았다. 아래는 실행할 때의 절차다.

1. Repl 에 이 폴더를 올린다. `replit.nix` 에 `pkgs.ffmpeg` 와 `pkgs.python311` 을 넣고 `pip install -r requirements.txt`.
2. `python tools/env_manifest.py --env-label "REPLIT/<repl-id>" env.json` 으로 환경을 기록한다. libx264 가 빠진 빌드면 엔진이 `CODEC_UNAVAILABLE` 로 멈춘다.
3. `python -m unittest discover -s tests -t tests` 를 돌린다.
4. `python tools/golden_run.py --env-label "REPLIT/<repl-id>" golden/` 를 돌리고 `golden/golden_summary.json` 을 HQ 로 돌려보낸다.
5. 출력 해시가 이 컨테이너의 값과 다를 수 있다. ffmpeg 빌드가 다르면 정상이다. 비교할 것은 `result: PASS`, `deterministic_output: true`, `checks` 전부 true 다.

공유 API 로 감쌀 때 필요한 것은 [REDTEAM.md](REDTEAM.md) 9절.

## HOLD

1. **Replit 실행 증거 없음.** 커넥터는 연결되어 있다(앱 목록 읽기 성공). 실행하려면 Replit Agent 로 기존 앱을 바꿔야 하고 크레딧이 든다. 사람 승인 전에는 하지 않는다.
2. 원격 URL 입력. 엔진 밖 수집기가 필요하다.
3. 공유 API 의 인증, 할당량, 동시성.
4. 격리 실행(별도 컨테이너, 비루트, 네트워크 차단, seccomp).
5. HQ 계약 원문. 이 엔진은 작업 지시서에 적힌 필드 이름(`video_uri`, `subtitles_json_or_srt`, `output_size`, `output_fps`, `safe_area`, `font_asset`, `job_id`)과 노션 FM v2 상태 계약(`ASSET_READY`)에 맞췄다. HQ 에 별도 JSON 스키마가 있으면 대조가 필요하다.
6. "FM 3.0" 이라는 이름의 시스템은 이 저장소와 노션 검색에서 찾지 못했다. 어떤 것도 수정하지 않았다.
