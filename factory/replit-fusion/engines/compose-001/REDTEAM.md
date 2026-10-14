---
engine: DF-ENGINE-COMPOSE-001
doc: redteam
status: draft
reviewed_at: 2026-10-14
reviewer: claude (architecture / security review 역할)
---

# 레드팀 검토 — DF-ENGINE-COMPOSE-001

이 엔진은 신뢰하지 않는 영상, 자막, 글꼴 경로를 받아 ffmpeg 을 실행한다. 아래 항목은 직접 공격해 보고 고친 것, 막은 것, 막지 못한 것이다.

판정 표기: **FIXED** 시험 중 실제로 뚫려서 고침 / **BLOCKED** 처음부터 막힘, 시험으로 확인 / **HOLD** 엔진 밖에서 막아야 함 / **RESIDUAL** 남는 위험.

## 시험 중 실제로 나온 결함

| # | 결함 | 어떻게 찾았나 | 처리 |
|---|---|---|---|
| F-1 | `.mp4` 로 위장한 HLS 재생목록이나 ffconcat 목록을 ffprobe 가 해석함. 재생목록 안의 `file:///etc/passwd` 를 열 수 있음 | 레드팀 설계 단계 | **FIXED**. ffmpeg 이 열기 전에 머리 바이트로 MP4/MOV 또는 EBML 만 통과시키고, probe 와 render 에서 demuxer 를 강제 (`media.sniff`). 시험 rt03, rt04 |
| F-2 | 자막마다 ffmpeg 입력을 하나씩 만들면, 자막 200개에서 38번째 입력 디코더가 `Resource temporarily unavailable` 로 실패 | 부하 시험 | **FIXED**. 자막 전체를 APNG 하나로 만들어 입력을 2개(원본 + 자막)로 고정. 시험 `test_200_cues_single_track_input` |
| F-3 | ffconcat 으로 PNG 를 묶으면 타임스탬프가 1/25초로 반올림 (0.3초 → 0.32초). 정밀도 옵션은 `-safe 1` 에서 금지 | 부하 시험 검사 실패를 추적 | **FIXED**. APNG(1/100000초 단위)로 교체. 안전 모드를 끄지 않음. 시험 `test_visible_only_inside_window` |
| F-4 | Pillow APNG `disposal=1` 이 빈 구간을 앞 프레임에 합쳐 자막이 0.1초 늦게 사라짐 | APNG 타임스탬프 실측 | **FIXED**. `disposal=0, blend=0` |
| F-5 | x264 `-threads 2` 에서 같은 입력의 출력 해시가 가끔 다름 (실측 1/17~1/60, 프레임 1개 내용 차이가 다음 참조 프레임까지 번짐) | 반복 시험에서 간헐 실패 | **FIXED**. 기본 `ffmpeg_threads=1`. 결과 JSON 에 `deterministic_mode` 기록. 필터 단계 150/150, x264 1스레드 100/100, 엔진 전체 30/30 같은 해시 |
| F-6 | 프레임 간격보다 짧은 자막은 화면에 한 번도 안 나올 수 있음 | 부하 시험 | **FIXED**. 경계 1ms 안쪽에 출력 프레임이 하나도 없으면 `CUE_SHORTER_THAN_FRAME` |
| F-7 | 자막 표시 검사가 작은 글자(32px)에서 틀린 실패를 냄 | 시험 | **FIXED**. 절대 오차 대신 원본 프레임 대조군과 비교. 음성 대조 시험 3개(자막 없음, 위치 틀림, 정상) |
| F-8 | ffmpeg 6.1 은 출력 파일이 이미 있으면 `File exists. Exiting.` 을 내고 **종료 코드 0** 을 돌려줌 | 재현 실험 중 발견 | **BLOCKED**. 엔진은 매번 새 임시 폴더에 쓰고, 성공 판정은 종료 코드가 아니라 ffprobe 검사로 함 |
| F-9 | moviepy 2.2.1 의 `moviepy.__version__` 이 `2.1.2` | 이전 증거 재검증 | 원본 태그 v2.2.1 의 `moviepy/version.py` 가 `2.1.2`, `pyproject.toml` 이 `2.2.1` 임을 확인. 상류 결함. 이 엔진은 moviepy 를 쓰지 않음 |

## 공격면별 판정

### 1. 명령 / 필터 주입

| 공격 | 판정 | 근거 |
|---|---|---|
| 자막 글자로 ffmpeg 필터 주입 (`'; drawtext=…`, `movie=/etc/passwd`) | **BLOCKED** | 자막은 Pillow 로 PNG 로 그린다. 필터 문자열에는 검증된 정수와 실수만 들어간다. 시험 rt01 이 argv 에 공격 문자열이 없음을 확인 |
| 셸 메타문자 파일명 (`-i evil;$(touch pwned)|x'.mp4`) | **BLOCKED** | `shell=False`, 인자 목록, 입력은 항상 `file:` 접두사. 시험 rt02 가 `pwned` 파일이 생기지 않음을 확인 |
| 스타일 필드로 주입 (`fill: "white:drawtext=…"`) | **BLOCKED** | 색은 `#RRGGBB` 정규식, 숫자는 범위 검사, 모르는 키는 거절 |
| 계약 밖 필드 (`extra_ffmpeg_args`) | **BLOCKED** | `UNKNOWN_FIELD` |

### 2. 경로와 원격 접근

| 공격 | 판정 | 근거 |
|---|---|---|
| `../` 경로 이탈, 절대 경로 `/etc/passwd` | **BLOCKED** | `realpath` 후 허용 루트 안인지 확인 |
| 루트 안의 심볼릭 링크가 밖을 가리킴 | **BLOCKED** | 최종 실제 경로로 판정. 시험 `test_symlink_escape` |
| FIFO, 폴더, 장치 파일 | **BLOCKED** | 일반 파일만 |
| `http(s)://`, `ftp://`, `concat:`, `data:`, `file://원격호스트` | **BLOCKED** | 스킴 허용 목록 + ffmpeg `-protocol_whitelist file` |
| 원격 영상을 받아야 하는 실제 운영 | **HOLD** | 엔진은 내려받지 않는다. 상위 수집기가 허용 도메인, 크기 한도, 콘텐츠 유형을 검사한 뒤 파일로 넘겨야 한다 |

### 3. 악성 미디어

| 공격 | 판정 | 근거 |
|---|---|---|
| 위장 재생목록 (HLS, ffconcat) | **FIXED** (F-1) | rt03, rt04 |
| 텍스트, PNG 를 `.mp4` 로 위장 | **BLOCKED** | rt05 |
| 잘린 MP4 | **BLOCKED** | rt06: 구조화 오류, 임시 폴더 없음, 결과 폴더 없음 |
| 오디오만 있는 MP4 | **BLOCKED** | rt07 `NO_VIDEO_STREAM` |
| 허용 밖 코덱 (예: 오래된 코덱의 파서 취약점) | **BLOCKED** | 영상 h264/hevc/vp8/vp9/av1/mpeg4/prores, 오디오 허용 목록만 |
| ffmpeg / libavcodec / Pillow 자체의 메모리 취약점 | **RESIDUAL** | 허용 목록으로 공격면을 줄였을 뿐 없애지 못한다. 운영에서는 네트워크 없는 별도 컨테이너, 비루트 사용자, seccomp 로 돌리고 ffmpeg 을 최신 보안 패치로 유지. 결과 JSON 에 ffmpeg 버전이 남는다 |

### 4. 자원 고갈

| 공격 | 판정 | 근거 |
|---|---|---|
| 큰 해상도 (4200x4200) | **BLOCKED** | 16.7M 픽셀 한도. rt08 |
| 긴 영상 | **BLOCKED** | 기본 180초. rt09 |
| 큰 파일 | **BLOCKED** | 기본 500MB. rt10 |
| 출력 폭주 | **BLOCKED** | `RLIMIT_FSIZE` → `OUTPUT_SIZE_LIMIT`. rt11 |
| 메모리 폭주 | **BLOCKED** | `RLIMIT_AS` (기본 4GB). rt12 는 48MB 로 묶어 깨끗하게 실패함을 확인 |
| 무한 실행 | **BLOCKED** | 벽시계 timeout 후 프로세스 그룹 전체 SIGKILL, `RLIMIT_CPU`. 시험 `test_timeout_rolls_back` |
| 자막 수 폭주 | **FIXED** (F-2) | 한도 200개, 입력 수 고정 |
| 동시에 여러 작업 | **HOLD** | 작업 하나의 한도만 있다. 동시 작업 수, 전체 디스크, 사용자별 할당량은 호출하는 쪽(큐)이 정한다 |

자원 실측 (이 컨테이너, 1080x1920 60fps 6초, 자막 200개): 렌더 8.2초, ffmpeg 최대 RSS 319MB, 파이썬 최대 RSS 251MB.

### 5. 글꼴

| 공격 | 판정 | 근거 |
|---|---|---|
| 바꿔치기한 글꼴 | **BLOCKED** | 요청에 sha256 을 고정하고 실제 파일과 비교 |
| 라이선스 없는 글꼴 | **BLOCKED** | OFL-1.1, Apache-2.0, MIT, UFL-1.0 만. 라이선스 파일도 허용 루트 안에 있어야 함 |
| 없는 글자 (두부 □) | **BLOCKED** | `GLYPH_MISSING`. Pillow `.notdef` 모양과 비교하는 휴리스틱 |
| 악성 글꼴 파일 (FreeType 파서 공격) | **RESIDUAL** | 해시 고정으로 운영자가 고른 글꼴만 쓰게 한다. 사용자가 글꼴을 올리게 하지 말 것 |

### 6. 자막 내용

| 공격 | 판정 | 근거 |
|---|---|---|
| 방향 재정의 문자 (U+202E), 제로폭 문자, 제어 문자 | **BLOCKED** | 유니코드 C 범주 전부 제거, NFC 정규화 |
| 지나치게 긴 자막 | **BLOCKED** | 200자, 3줄, 안전 영역 높이 |
| 겹치는 시간, 영상 끝 뒤의 자막 | **BLOCKED** | `CUE_OVERLAP`, `CUE_AFTER_END` |
| 유해·허위 문구 | **HOLD** | 엔진은 내용을 판단하지 않는다. 발행 전 Human Gate 가 본다 |

### 7. 출력 무결성과 롤백

| 항목 | 판정 | 근거 |
|---|---|---|
| 실패 중간 산출물 | **BLOCKED** | 임시 폴더에서 만들고, 모든 검사가 통과한 뒤에만 `<out>/<job_id>` 로 이름을 바꾼다. 실패하면 임시 폴더를 지우고 `_failed/` 에 결과 JSON 만 남긴다 |
| 같은 job_id 재실행으로 덮어쓰기 | **BLOCKED** | `JOB_EXISTS`. 기존 결과 바이트가 그대로인지 시험 |
| 롤백 (승인 후 되돌리기) | **HOLD** | 엔진 결과는 불변 폴더다. 되돌리기는 호출 쪽이 이전 job_id 를 다시 가리키면 된다. 엔진은 지우지 않는다 |

### 8. 출처 (provenance)

결과 JSON 에 남는 것: 계약 버전, 엔진 ID·버전·git 커밋·dirty 여부, 요청 정규화 sha256, 입력 sha256, 글꼴 sha256·라이선스, 자막 정규화 sha256, 출력 sha256, ffmpeg 버전, Pillow·파이썬 버전, 실행 환경 라벨, ffmpeg argv, 구조화 stderr, 시각.

**RESIDUAL**: argv 와 결과에 절대 경로가 들어간다. 결과 JSON 을 외부 고객에게 그대로 보이면 서버 경로가 드러난다. API 로 감쌀 때는 `render.argv` 와 경로를 걸러서 보낼 것.

### 9. 공유 API 로 감쌀 때 (Replit 등)

엔진은 라이브러리와 CLI 다. HTTP 서버가 없다. 다른 팀이 공유 API 로 감싸면 아래가 필요하다. 지금은 모두 **HOLD**.

1. 인증과 호출자별 할당량. 엔진 안에는 인증이 없다.
2. 호출자별 허용 루트와 출력 폴더. job_id 는 호출자 이름공간을 붙여 충돌을 막는다.
3. 작업 큐와 동시 실행 한도. 작업마다 최대 4GB 주소 공간과 CPU 를 쓸 수 있다.
4. `preexec_fn` 은 다중 스레드 서버 안에서 안전하지 않다(파이썬 문서 경고). 웹 서버 스레드에서 직접 부르지 말고 별도 작업 프로세스에서 부를 것.
5. 원격 URL 수집기는 엔진 밖에 두고, SSRF 를 막을 것(사설 IP, 메타데이터 주소 차단).
6. stderr 와 경로는 내부 로그에만 두고 외부 응답에서는 오류 코드만 보낼 것.

## 남은 위험 요약

1. ffmpeg / Pillow / FreeType 파서 취약점 — 격리 실행 필요
2. 공유 API 의 인증, 할당량, 동시성 — 감싸는 쪽 책임
3. 결과 JSON 의 절대 경로 노출
4. 자막 표시 검사와 없는 글자 검사는 휴리스틱이다. 둘 다 실패 쪽으로 닫힌다(판정이 애매하면 FAILED)
5. 결정론은 같은 ffmpeg 빌드 안에서만 보장된다. 다른 빌드(Replit Nix 의 ffmpeg 등)에서는 해시가 다를 수 있고, 그것은 결함이 아니다
