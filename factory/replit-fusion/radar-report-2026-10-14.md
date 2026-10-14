---
registry: DF-REG-REPLIT-FUSION-FACTORY-001
lot: DF-REPLIT-GITHUB-PARTS-FUSION-001
report: radar-report-2026-10-14
status: draft
worker: claude (architecture / security review 역할)
golden_test: DF-GT-VIDEO-001 PASS, DF-GT-VIDEO-002 PASS
replit_execution: not_verified
---

# GitHub Parts Radar 첫 실행 보고 — 2026-10-14

## 1. 현재 공정

MASTER WORK ORDER v1.0 의 STEP 1~8 을 한 번 돌렸다. 첫 GOLDEN TEST 는 컨테이너 실행까지 PASS 했다. Replit 실행은 아직 하지 않았다.

판정: **RESEARCH PASS + EXECUTION PASS (Linux 컨테이너) / REPLIT HOLD**

## 2. 실제 완료한 작업

1. 기억 복구. 노션에서 아래 기록을 직접 읽었다.
   - `DREAM FACTORIES — REPLIT VISUAL COMMAND OS HANDOFF 2026-10-13`
   - `FM v2 · DREAM LOOP TREE VIDEO FACTORY — Remotion + KIE SAFE DOCK v0.1`
   - `DREAM OS 3.4 이후 개발 로드맵 — 기억복구·실측 20261014`
   - 검색 결과로 FM v2 SCOPE FREEZE / FM v3 BACKLOG, MULTI-6 SLIM SAFE DOCK, SOPHIE / F30 기록의 존재를 확인했다.
2. 중복 제거. 아래 표 참고.
3. GitHub 저장소 24개를 얕게 복제해 HEAD 의 LICENSE 와 README 를 직접 읽었다. 22개를 부품으로 등록했다. 2개(rhasspy/piper, ControlNet-v1-1-nightly)는 이전된 저장소이거나 보조 저장소라 다른 부품의 근거로만 썼다.
4. 모델 가중치 라이선스 10건을 Hugging Face 메타데이터와 LICENSE 파일로 확인했다.
5. 영상 편집 후보 3개(MoviePy, auto-editor, editly)를 비교하고 MoviePy 를 골랐다.
6. MoviePy 와 auto-editor 를 실제로 설치하고 실행했다. 증거 JSON 과 프레임 이미지를 남겼다.
7. 부품 등록부, Replit 창고 설계, 이 보고서를 작성했다.

### 중복 제거

| 작업 지시 항목 | 기존 기록 | 처리 |
|---|---|---|
| Remotion | FM v2 SAFE DOCK 에서 REMOTION ADAPTER 후보 | 다시 조사하지 않음. 라이선스 조건만 등록부에 추가 |
| Postiz 연동 | 거버넌스상 PUBLISHING 레일, Postiz MCP 연결됨 | EXISTING_RAIL 로 등록. 새 연동을 만들지 않음 |
| Replit UI 구조 | Visual Command OS Handoff (SvelteKit + Svelte Flow, 교체 가능한 DB) | 같은 결정을 따름. 창고는 그 OS 의 왼쪽 패널 |
| 생성 도구 계약 | FM v2 MACHINE LINE / ADAPTER, 상태 계약 | 같은 상태 계약을 씀 |
| "FM 3.0 SLIM" | 노션에서 이 이름은 찾지 못함. FM v2(마감 중), FM v3(백로그), MULTI-6 SLIM 은 있음 | 이름 확인을 HOLD 로 둠. 어느 쪽도 수정하지 않음 |

## 3. 발견한 기술

전체 필드는 [parts-registry.json](parts-registry.json) 에 있다.

### A. YouTube / Media

| ID | 부품 | 코드 라이선스 | 가중치·약관 | 마지막 커밋 | 레벨 |
|---|---|---|---|---|---|
| VID-001 | MoviePy | MIT | 없음 | 2026-08-26 | **L2** |
| VID-002 | auto-editor | Unlicense | 없음 | 2026-10-12 | **L2** |
| VID-003 | editly | MIT | 없음 | 2025-02-20 | L1 |
| VID-004 | Remotion | Remotion License | 없음 | 2026-10-13 | L1 (FM v2 중복) |
| VID-005 | FFmpeg | LGPL/GPL | 없음 | 2026-10-14 | 인프라 |
| SUB-001 | faster-whisper | MIT | Whisper MIT / apache-2.0 | 2026-10-10 | L1, 다음 후보 |
| SUB-002 | whisperX | BSD-2 | pyannote 게이트 모델 | 2026-09-26 | L1 |
| SUB-003 | Whisper | MIT | MIT / apache-2.0 | 2026-08-31 | L1 |
| TTS-001 | Kokoro | Apache-2.0 | Apache-2.0 | 2025-08-06 | L1, 한국어 없음 |
| TTS-002 | Coqui XTTS-v2 | MPL-2.0 | **CPML 비상업** | 2024-02-10 | 상업 불가 |
| TTS-003 | Piper | GPL-3.0 | 목소리별 | 2026-10-10 | L1 |
| AUTO-001 | MoneyPrinterTurbo | MIT | 외부 API 약관 | 2026-10-14 | 참고용 |
| PUB-001 | Postiz | AGPL-3.0 | 없음 | 2026-10-12 | 기존 레일 |
| RES-001 | yt-dlp | Unlicense | YouTube 약관 | 2026-10-10 | 법무 HOLD |

### B. AI Character

| ID | 부품 | 코드 | 가중치 / 숨은 의존성 | 상업 판정 |
|---|---|---|---|---|
| CHR-001 | ComfyUI | GPL-3.0 | 모델별 | 실행기. 외부 GPU 전용 |
| CHR-002 | PhotoMaker | Apache-2.0 | V2 apache-2.0, 그러나 **insightface 사용** | HOLD |
| CHR-003 | InstantID | Apache-2.0 | README: 체크포인트 **연구 전용**, insightface antelopev2 | 불가 |
| CHR-004 | PuLID | Apache-2.0 | apache-2.0, **insightface 사용**, FLUX 판은 FLUX.1-dev 조건 추가 | HOLD |
| CHR-005 | ControlNet | Apache-2.0 | OpenRAIL | 후보 |
| CHR-006 | IP-Adapter | Apache-2.0 | FaceID 는 라이선스 표기 없음 + insightface | FaceID 불가 |
| CHR-007 | InfiniteYou | Apache-2.0 | **CC-BY-NC-4.0** | 불가 |
| CHR-008 | InsightFace | MIT | 모델은 **비상업 연구 전용** | 차단 요인 |

### 가장 중요한 발견

정체성 보존 부품 5개(PhotoMaker V2, InstantID, PuLID, IP-Adapter-FaceID, InfiniteYou)는 모두 insightface 얼굴 모델을 쓴다. 코드는 Apache-2.0 이지만 insightface 모델은 비상업 연구 전용이다.

**코드 라이선스 ≠ 모델 가중치 라이선스** 원칙이 실제로 판정을 바꾼 사례다. 오픈소스만으로 상업용 캐릭터 공장을 만들 수는 없다. insightface 상업 라이선스를 사거나, Higgsfield 같은 상용 API 의 약관 안에서 만들어야 한다.

## 4. 검증 결과

### FIRST GOLDEN TEST

| 조건 | 결과 | 근거 |
|---|---|---|
| 영상 편집 오픈소스 3개 검색 | PASS | MoviePy, auto-editor, editly (+ FM v2 의 Remotion) |
| 기능 비교 | PASS | 아래 표 |
| 실제 GitHub 소스 확인 | PASS | HEAD SHA 기록 (등록부 `HEAD_SHA`) |
| 실제 라이선스 확인 | PASS | LICENSE 원문 첫 줄 직접 읽음 |
| 1개 선정 | PASS | MoviePy |
| 최소 실행 테스트 | PASS | DF-GT-VIDEO-001 |
| 실행 증거 확보 | PASS | evidence JSON, sha256, ffprobe, 프레임 PNG |
| Replit 연동 가능성 검증 | **분석만 PASS / 실행 HOLD** | Replit 에서 실행하지 않음 |

### 비교와 선정

| 기준 | MoviePy | auto-editor | editly |
|---|---|---|---|
| 하는 일 | 범용 편집, 합성, 자막 | 무음 구간 자동 삭제 | JSON 선언형 편집, 전환 효과 |
| 언어 | Python | Nim 바이너리 + pip 래퍼 | Node.js |
| 네이티브 의존성 | 없음 (휠에 ffmpeg 동봉) | 첫 실행 때 바이너리 다운로드 | headless-gl, canvas 빌드 |
| 활동 | 2026-08-26 | 2026-10-12 | 2025-02-20 |
| Replit 예상 | 높음 | 중간 | 낮음~중간 |
| 실행 시험 | PASS | PASS | 하지 않음 |

MoviePy 를 고른 이유. 의존성이 가장 적고, 쇼츠 재가공에 필요한 크롭·리사이즈·자막·합성을 한 부품이 한다. 실제 쓰임새도 있다. MoneyPrinterTurbo 가 `moviepy==2.2.1` 을 고정해서 쓴다.

### DF-GT-VIDEO-001 (MoviePy 2.2.1)

합성 원본만 썼다. 외부 영상, 유료 API, 네트워크는 쓰지 않았다.

- 입력: 1280x720, 6.0초, H.264 + AAC, 2~3초 무음. sha256 `106c37a3…`
- 처리: 무음 구간 삭제 → 가운데 9:16 크롭 → 540x960 → 한국어 제목·자막 합성
- 출력: 540x960, H.264 + AAC, 약 5.0초. sha256 `af839bdf…`
- 검사 4개 모두 true. 소요 7.36초 (원본 생성 포함, 시험 컨테이너 기준)
- 같은 스크립트를 두 번 돌렸을 때 원본 파일 해시가 같았다.
- 기록: [evidence/DF-GT-VIDEO-001.json](golden-test/evidence/DF-GT-VIDEO-001.json), 프레임 [short_frame_t2.png](golden-test/evidence/short_frame_t2.png)

![t=2초 프레임](golden-test/evidence/short_frame_t2.png)

발견한 결함. MoviePy 2.2.1 패키지의 `moviepy.__version__` 은 `2.1.2` 다. 처음 기록이 2.1.2 로 잘못 남아서, 설치 메타데이터를 정본으로 쓰도록 스크립트를 고치고 다시 돌렸다. 두 값을 모두 증거에 남겼다.

### DF-GT-VIDEO-002 (auto-editor 29.3.1)

- 같은 원본에서 무음 구간을 자동 삭제했다. 6.0초 → 5.17초.
- pip 패키지는 첫 실행 때 GitHub releases 에서 linux-x86_64 바이너리를 내려받는다. Replit 에서 확인할 점이다.
- 기록: [evidence/DF-GT-VIDEO-002.json](golden-test/evidence/DF-GT-VIDEO-002.json)

## 5. Replit 적용 가능성

| 부품 | 판단 | 이유 |
|---|---|---|
| MoviePy | 높음 (예상) | 순수 파이썬, ffmpeg 동봉. CPU 만 씀 |
| auto-editor | 중간 (예상) | 바이너리 다운로드가 필요함 |
| faster-whisper | 중간 (예상) | CPU 가능. 작은 모델만 |
| editly, Remotion | 낮음~중간 | 네이티브 GL / Chromium |
| ComfyUI 와 캐릭터 부품 전부 | Replit 불가 | GPU 필요. Replit 은 API 클라이언트만 하고 외부 GPU 워커에 맡긴다 |

Replit 상태. 연결된 계정의 편집 가능한 앱은 5개이고, 모두 자동 생성 이름이다(`SuspiciousDrabScandisk` 등). DREAM 이름의 앱은 없다. 로드맵 규칙(기존 앱 ID 확보 전 신규 생성 금지)에 따라 새로 만들지 않았다.

설계: [replit-warehouse-design.md](replit-warehouse-design.md)

## 6. 비용 / 제약

- 이번 작업의 유료 호출: 0. GPU 사용: 0. Replit 앱 생성: 0.
- 성능 수치는 시험 컨테이너 한 번의 측정값뿐이다. Replit 수치가 아니다.
- STARS/FORKS 는 비워 두었다. 이 환경에서 api.github.com 과 github.com 페이지가 403 이다. 지어내지 않았다.
- FLUX.1-dev 라이선스 원문은 게이트 때문에 읽지 못했다. 등록부에 미확인으로 적었다.
- Remotion 은 법인 직원이 4명 이상이면 Company License 가 필요하다. 회사 규모는 확인하지 않았다.
- Postiz 는 AGPL-3.0 이다. 수정해서 서비스로 배포하면 소스 공개 의무가 생긴다.

## 7. Evidence

| 증거 | 경로 |
|---|---|
| MoviePy 실행 기록 | `factory/replit-fusion/golden-test/evidence/DF-GT-VIDEO-001.json` |
| auto-editor 실행 기록 | `factory/replit-fusion/golden-test/evidence/DF-GT-VIDEO-002.json` |
| 출력 프레임 | `factory/replit-fusion/golden-test/evidence/short_frame_t2.png` |
| 재현 스크립트 | `factory/replit-fusion/golden-test/moviepy_smoke.py` |
| 부품 등록부 | `factory/replit-fusion/parts-registry.json` |

mp4 파일은 커밋하지 않았다. 스크립트를 다시 돌리면 원본은 같은 해시로 다시 만들어진다.

## 8. HOLD 항목

1. Replit 실제 실행. 기존 앱을 쓸지, 새 앱을 만들지(비용 가능) 사람이 정해야 한다.
2. "FM 3.0 SLIM" 이름. 노션에서 찾지 못했다. FM v2, FM v3 백로그, MULTI-6 SLIM 중 무엇인지 확인이 필요하다.
3. 캐릭터 정체성 부품 상업화. insightface 상업 라이선스 또는 상용 API 경로를 정해야 한다.
4. 기존 canonical 저장소 `dream-factories/dream-factory-control-center`. 이 세션 범위 밖이고, 노션 기록상 조직 OAuth 403 이다. 읽지 않았다.
5. 이 폴더를 main 에 넣을지. 이 저장소는 승인 페이퍼만 두는 공개 자료방이다. 사람이 정한다.
6. MULTI-6 다중 AI 조사. Gemini, Grok, Manus 를 실제로 부르지 않았다. 이번 결과는 Claude 단독이다. 다른 AI 의 판정은 SIMULATED 도 아니고 없음이다.
7. yt-dlp. 타인 영상 다운로드의 약관·저작권 판단.

## 9. 다음 공사

**faster-whisper 로 자막 부품 L2 검증.**

같은 합성 원본에 사람 목소리 대신 공개 라이선스 음성 샘플을 넣고, CPU 에서 `base` 모델로 SRT 를 만든다. 그 SRT 를 VID-001 의 자막 입력으로 넣는다. 두 부품을 이은 첫 조립(VID-002 → SUB-001 → VID-001)이 된다.

## 10. 남은 공사

| 우선순위 | 공사 | 완료 기준 |
|---|---|---|
| P1 | 자막 부품 L2 | faster-whisper SRT + MoviePy 합성 증거 |
| P2 | Replit 실행 | 기존 앱 하나에서 DF-GT-VIDEO-001 재실행, 해시와 ffprobe 비교 |
| P3 | 창고 패널 | Visual Command OS 왼쪽 패널에 등록부 카드 표시 |
| P4 | FM 에 부품 1개 연결 | FM MEDIA JOB ROUTER 에 MACHINE LINE 하나, FM 코드 변경 없음 |
| P5 | 제품·사업성 | 아래 표의 판정을 실제 원가로 다시 |
| — | 캐릭터 라인 | insightface 라이선스 결정 전 착수하지 않음. FM 완주 전 대량 생성 금지 |

### 제품별 라이선스 1차 판정

비용과 판매 가능성은 아직 근거가 없어 적지 않는다.

| 제품 | 라이선스상 상업 이용 | 막는 것 |
|---|---|---|
| 1. Shorts Automation | 가능 (MoviePy, auto-editor, faster-whisper) | 한국어 TTS 부품 없음 |
| 2. Character Studio | 오픈소스 경로로는 불가 | insightface, CC-BY-NC 가중치 |
| 3. Video Editing | 가능 | 없음 (Remotion 쓰면 회사 규모 확인) |
| 4. Publishing | 기존 Postiz 레일 | AGPL, 사람 승인 |
| 5. Business Research | 미조사 | — |
| 6. Agent / MCP | 미조사 | — |

---

다음공사 ㄷㅇㄱㅅ: faster-whisper 자막 부품 L2 검증 → VID-002 → SUB-001 → VID-001 첫 조립

남은공사 ㄴㅇㄱㅅ: Replit 실행(P2), 창고 패널(P3), FM 부품 연결(P4), 사업성(P5), HOLD 7건

클릭 몇번: 0 — 다음 공사는 무료 CPU 로 이 저장소 안에서 끝난다. Replit 실행은 앱 선택 1회 필요

해결경로: GitHub 원본 → 라이선스 원문 → 컨테이너 실행 → evidence JSON → 등록부 → (사람 승인) → Replit → FM MACHINE LINE

실행명령 ㅋ0: Human Gate 전까지 다음 공사(자막 부품 L2)를 진행. Replit 앱 생성, 유료 API, GPU, 발행은 멈춘다
