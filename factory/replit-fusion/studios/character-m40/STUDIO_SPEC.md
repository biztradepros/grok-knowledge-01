---
lot: DF-DCL-M40-CHARACTER-STUDIO-001
title: AI CHARACTER DEVELOPMENT STUDIO — M40
status: draft
reviewer: claude (보안·데이터 계약 역할)
date: 2026-10-14
verdict: DESIGN PASS · HIGGSFIELD READ/QUOTE PASS · IDENTITY EVAL ENGINE PASS (sandbox) · GENERATION HOLD · INTEGRATION HOLD
---

# AI CHARACTER DEVELOPMENT STUDIO — M40

## 0. 이번에 실제로 확인한 사실

| 항목 | 결과 | 근거 |
|---|---|---|
| 참조 이미지 3장 | **이 세션에 없음.** 업로드 폴더에 이미지가 없다 | 얼굴 분석은 하지 않았다. 아래 1절은 분석 틀이다 |
| Higgsfield 잔액 | 145.53 크레딧, Starter | `evidence/higgsfield_api_readonly_20261014.json` |
| Reference Element | `SOPHIE_V1_1` (`bfb09299-…`) 1개뿐 | 같은 파일 |
| F30 | Higgsfield 에 Element·Soul 없음 | 같은 파일. F30 의 원본 위치 확인 필요 |
| Soul 캐릭터 | 0개 | 같은 파일 |
| M40 후보 4장 견적 | **4.5 크레딧**, `submitted: false` (작업 없음) | `ai_influencer_prepare` |
| 캐릭터 제어 방식 | 성별·나이·눈 모양 같은 **이산형 특징 선택**과 글 설명뿐. "연예인 A 60% + B 40%" 같은 혼합 비율 제어는 API 에 없다 | `ai_influencer_get_options` |
| FM 3.0 | n8n 에 `DREAM FM 3.0 SOPHIE DUPLICATE GUARD 001` 있음 (비활성). 이전 보고의 "FM 3.0 못 찾음"을 정정한다. 건드리지 않았다 | n8n `search_workflows` |
| 얼굴 일관성 평가기 | 시험 11개 PASS (Python 3.11, OpenCV 4.10) | `identity-eval/` , `evidence/identity_eval_tests.log` |
| 스키마 | 시험 6개 PASS | `schema/test_schemas.py` |
| Higgsfield 미디어 내려받기 | **실패.** CloudFront 두 도메인이 이 환경 네트워크 정책에서 403 | SOPHIE 실이미지 보정 시험 HOLD |

## 1. 얼굴 설계 요구사항 분석 틀 (목표 1)

참조 이미지가 들어오면 아래 순서로만 본다. 사람을 복제하지 않고 **속성만** 뽑는다.

1. **권리 분류 먼저.** 각 이미지를 `reference.schema.json` 으로 등록한다. 알아볼 수 있는 실존 인물이면 `allowed_use` 는 `text_brief_only` 또는 `forbidden` 만 가능하다(스키마가 강제).
2. **속성 추출.** 얼굴형, 눈 모양, 눈썹 두께, 수염, 머리 길이·색, 나이 인상, 체형, 스타일링, 표정, 조명. 결과는 Higgsfield `selection` 키(예: `es_almond`, `fh_stubble`)와 짧은 형용사로만 적는다.
3. **분위기 추출.** 프리미엄 자동차 라이프스타일에 필요한 것: 절제, 신뢰, 여유, 손·소매·시계 같은 디테일, 실내·드라이빙 조명.
4. **금지 기록.** 이름, 특정인의 고유 특징(점 위치, 흉터, 독특한 헤어라인 조합)은 `face_design.avoid` 에 넣는다.

"연예인 혼합 비율"을 요청받으면: 그런 제어는 없다고 답하고, 원하는 인상을 특징 선택과 형용사로 바꿔 적는다. 비율 숫자는 데이터에 남기지 않는다.

## 2. 원작 상업 캐릭터 정의 (목표 2)

초안: `schema/examples/m40.character.json`

| 항목 | 값 |
|---|---|
| ID | `DF-CHAR-M40` |
| 해석 | **가정:** F30 과 같은 규칙으로 M40 = 40대 남성. 확인 필요 |
| 역할 | 프리미엄 자동차 라이프스타일 호스트 |
| 톤 | 차분함, 신뢰, 절제된 고급감 |
| 특징 선택 | male, mature, east_asian, short dark brown hair, stubble, athletic, tall, suits |
| 보호 대상 | SOPHIE_V1_1, F30 — 평가기에서 겹치면 차단 |
| 금지 | 실존 인물 닮게 만들기, 자동차 브랜드 로고 무단 사용 |

## 3. ARCHITECTURE

새 Replit 앱을 만들지 않는다. 기존 DREAM VISUAL COMMAND CENTER(노션 작업지시서 2026-10-14, IC-0~IC-6) 의 인물 노드 상세 패널에 "Studio" 탭을 붙인다.

```
DVCC 무한 캔버스 (기존)
 └─ 인물 노드 M40 ──▶ Studio 탭
       │ ① References   ② Brief/Traits   ③ Candidates   ④ Consistency   ⑤ Versions/LOCK   ⑥ Higgsfield
       ▼
기존 Replit API (중간 관제, 앱 ID 확인 필요)
 ├─ quote      → Higgsfield ai_influencer_prepare / 견적 (무료)
 ├─ generate   → Human Gate(크레딧 승인) → Higgsfield generate_* / ai_influencer_generate
 ├─ evaluate   → DF-ENGINE-IDENTITY-001 (CPU, OpenCV)
 ├─ lock       → MASTER LOCK 기록 (사람 승인 필수)
 └─ return     → n8n AI RESULT INBOX (기존, 인증 추가 후) → GPT REVIEW (기존 MEDIA FACTORY CONTROL FLOW)
저장
 ├─ GitHub(공개): 스키마, 평가 결과 JSON, 해시, 생성 ID — 이미지·얼굴 벡터 없음
 ├─ 비공개 버킷: 참조 원본, 후보 이미지
 ├─ Supabase: characters / references / candidates / evaluations / master_locks
 └─ Notion: 캐릭터 프로필, 승인 기록
```

재사용 자산:

| 자산 | 위치 | 쓰임 |
|---|---|---|
| AI RESULT INBOX | n8n `NoCI39P8xY6atK9s` (활성) | 생성·평가 결과 수신. **현재 무인증** |
| MEDIA FACTORY CONTROL FLOW v0.1 | n8n `IGpSQaRV8SdkNRfo` (활성) | RESULT_READY → GPT REVIEW |
| FM V2 MEDIA PREUPLOAD GOLDEN | n8n `N8uJdgsbQs4pIN1v` | "identity QA HOLD" 칸에 평가기를 붙인다 |
| FM 3.0 SOPHIE DUPLICATE GUARD | n8n `DIHXv607nEFxctFc` | 같은 fail-closed 방식을 캐릭터 중복 방지에 따른다. 수정하지 않음 |
| SOPHIE_V1_1 Element | Higgsfield | 보호 대상. 읽기만 |
| DF-ENGINE-COMPOSE-001 | 이 저장소 | MASTER 확정 뒤 쇼츠 자막 합성 |

다중 AI 역할(노션 DVCC 규칙): ASTRA=구조·사업성, Claude=보안·데이터 계약(이 문서), Gemini=저비용 자동화, Grok=콘텐츠 전략, Cursor/Codex=구현, GPT HQ=최종 판정. 이번에 다른 AI 는 부르지 않았다. 그들의 검토는 **없음**이지 SIMULATED 도 아니다.

## 4. ENGINE COMPARISON

### 4.1 생성 방식

| 방식 | 하는 일 | 일관성 | 비용(실측 단가) | 권리 | 판정 |
|---|---|---|---|---|---|
| **A. Higgsfield AI Influencer Sheet** | 특징 선택 + 설명 → 캐릭터 시트 | 시트 안에서는 같은 얼굴 | 1장 1.12, 4장 견적 4.5 | Higgsfield 약관 따름(상업 범위 확인 필요) | **1단계 후보 생성에 사용** |
| **B. Reference Element** | MASTER 1장 → `<<<element_id>>>` 로 여러 모델에 주입 | 모델 의존. SOPHIE 에 이미 쓰는 방식 | Element 생성 비용 미확인, 이미지 0.25~2.5 | 같음 | **MASTER 이후 생산에 사용** |
| **C. Soul 2.0 학습** | 같은 인물 5~20장 → soul_id | 높다고 안내됨, Soul V2/Cinema 모델만 | 학습 비용 **미확인** (견적 API 없음) | 같음 | 생산량이 늘면 검토 |
| **D. 편집(이미지 편집 모델)** | 후보 한 장을 고쳐 다음 라운드 | 원본을 기준으로 유지 | GPT Image 2.5 0.25~1 | 같음 | **2라운드 미세 수정에 사용** |
| **E. ComfyUI + IP-Adapter / PuLID (외부 GPU)** | 오픈소스 정체성 보존 | 높음(논문 주장, 미검증) | GPU 시간 비용 별도 | **insightface 비상업 모델 의존** | **HOLD** |

### 4.2 오픈소스 부품 라이선스 (GitHub 원문 확인, 2026-10-14)

| 부품 | 코드 | 가중치·의존성 | 상업 판정 |
|---|---|---|---|
| ComfyUI | GPL-3.0 | 모델별 | 내부 서비스 실행은 가능. 배포 시 GPL 의무 |
| cubiq/ComfyUI_IPAdapter_plus | GPL-3.0 | 기본 IP-Adapter 가능, FaceID 계열은 insightface | FaceID 불가 |
| cubiq/PuLID_ComfyUI | Apache-2.0 | PuLID 가중치 apache-2.0, **insightface antelopev2 + EVA-CLIP** | insightface 때문에 HOLD |
| balazik/ComfyUI-PuLID-Flux, lldacing/ComfyUI_PuLID_Flux_ll | Apache-2.0 | 위 + **FLUX.1-dev**(게이트, 원문 미확인) | HOLD |
| tencent-ailab/IP-Adapter | Apache-2.0 | FaceID 는 insightface | FaceID 불가 |
| InstantID / PhotoMaker V2 / InfiniteYou | Apache-2.0 | 연구 전용 체크포인트 / insightface / CC-BY-NC | 불가 |

결론: 오픈소스만으로 상업용 정체성 보존 생성을 하려면 insightface 상업 라이선스가 필요하다. 지금은 **Higgsfield 를 생성 엔진**, **오픈소스는 평가에만** 쓴다.

### 4.3 일관성 평가 모델

| 후보 | 라이선스 | 판정 |
|---|---|---|
| **OpenCV zoo YuNet(검출) + SFace(인식)** | MIT / Apache-2.0 (모델 폴더별 LICENSE) | **채택.** CPU, 39MB, 해시를 LFS 포인터와 대조 |
| dlib face recognition ResNet v1 | 제작자가 퍼블릭 도메인 선언 | 예비. 단 68점 랜드마크 모델은 비상업 |
| insightface buffalo_l / antelopev2 | 모델 비상업 연구 전용 | 불가 |
| facenet-pytorch (VGGFace2 / CASIA) | 코드 MIT, 학습 데이터 조건 불명확 | HOLD |
| AdaFace (WebFace4M 등) | 코드 MIT, 데이터 비상업 | HOLD |
| deepface | MIT 래퍼, 안쪽 모델 라이선스 따름 | 직접 쓰지 않음 |

남는 위험: SFace 의 학습 데이터 출처는 README 에 적혀 있지 않다. 배포 라이선스(Apache-2.0)를 근거로 쓰되 RESIDUAL 로 남긴다.

## 5. UI SPECIFICATION (DVCC 안의 Studio 탭)

| 패널 | 내용 | 동작 |
|---|---|---|
| ① References | 참조 카드(썸네일은 비공개 버킷 서명 URL), 권리 배지 OWNED / LICENSED / UNVERIFIED / PROHIBITED, 허용 용도 | 실존 인물이면 "얼굴 입력" 토글 비활성. 등록 시 sha256 계산 |
| ② Brief / Traits | Higgsfield 특징 칩(성별, 나이, 머리, 수염…) + 한 줄 설명 + 금지 목록 | "연예인 %" 입력란은 만들지 않는다. 사람 이름이 들어가면 경고 |
| ③ Candidates | 4열 그리드, 라운드 탭, 카드마다 모델·시드·비용·generation_id·평가 배지 | 2~4장 선택 → 나란히 비교, A/B 토글, 확대 시 얼굴 영역 동기 확대. 점수 1~5 (brief_fit, premium_feel, distinctiveness, likeness_risk). keep / reject / iterate |
| ④ Consistency | 후보 × MASTER 코사인 표(색 구간 PASS/REVIEW/FAIL), 보호 대상 열(SOPHIE, F30) | 보호 대상 열이 기준을 넘으면 LOCK 버튼 잠김. policy 값과 calibrated 여부 표시 |
| ⑤ Versions / LOCK | 버전 타임라인 v0.x 탐색 → v1.0.0 LOCK, supersedes 선 | LOCK 대화상자: 권리 체크 4개 + 사람 승인. GPT HQ 승인만으로는 잠기지 않음 |
| ⑥ Higgsfield | 잔액, 견적, 승인 대기, 진행 중 작업, 결과 generation_id, Element/Soul ID | "견적 받기"는 바로, "생성"은 승인 버튼 뒤. 크레딧 상한 입력 |

상태 표기: `DEMO` / `IMPORTED` / `LIVE_VERIFIED` (DVCC 규칙과 같음). API 를 실제로 부르지 않은 값은 LIVE_VERIFIED 가 될 수 없다.

## 6. DATA SCHEMA

`schema/` 의 JSON Schema 2020-12 네 개. 규칙은 문서가 아니라 스키마가 막는다.

| 스키마 | 핵심 규칙 (`test_schemas.py` 로 확인) |
|---|---|
| `character.schema.json` | 얼굴 설계는 속성만, 보호 대상 목록, 버전 목록 |
| `reference.schema.json` | 실존 인물 → 얼굴 입력 불가. 권리 미확인 → 글 설명까지만 |
| `candidate.schema.json` | 생성 이후 상태는 비용 승인자·시각이 있어야 함. 견적과 실제 크레딧 분리 |
| `master_lock.schema.json` | 사람 소유자 승인 필수, 권리 체크 4개 모두 true, `immutable: true`, 바꾸려면 새 버전 + supersedes |

Supabase 테이블은 스키마와 1:1: `characters`, `references`, `candidates`, `evaluations`, `master_locks`, `approvals`. 키는 노션 DVCC 의 안정 ID 규칙(`CREATOR_ID`, `JOB_ID`, `EVIDENCE_ID`)과 이어 붙인다: `character_id` ↔ `CREATOR_ID`.

## 7. IMPLEMENTATION PLAN

| 단계 | 일 | 완료 기준 | 비용 |
|---|---|---|---|
| S0 (완료) | 기존 자산 읽기, 라이선스, 평가기, 스키마 | 이 커밋 | 0 |
| S1 | 참조 3장 업로드 → 권리 분류 → 속성 브리프 | reference 3건 등록, 사람 확인 | 0 |
| S2 | 네트워크 허용 후 SOPHIE 9장으로 평가기 보정 (T-3) | 보정 리포트, policy `calibrated=true` | 0 |
| S3 | 라운드 1: AI Influencer 시트 4장 | 승인 → generation_id 4개, 평가 JSON | 4.5 |
| S4 | 라운드 2: 상위 2장 편집 변형 8장 | 승인 → ID 8개, 비교·점수 | 2~8 |
| S5 | MASTER 후보 4방향(정면, 좌우 3/4, 전신) → LOCK | 내부 유사도 최소값, 보호 대상 분리, 사람 승인 | 4~10 |
| S6 | LOCK 이미지로 Reference Element 생성 → 시험 컷 6장 + 영상 1편 | element_id, 시험 컷 평가 PASS 비율 | 6~15 |
| S7 | DVCC Studio 탭 구현 (기존 Replit 앱) | 기존 앱 ID 확정 후, UI 수용 시험 T-8 | 0 (Replit 플랜 내) |
| S8 | n8n 결과 반환 (인증 추가 후) | 같은 JOB_ID 로 수신 → 원장 → 재조회 | 0 |

## 8. COST ESTIMATE

크레딧 단가는 이 계정의 실제 사용 내역에서 가져왔다(2026-10-07~14). 크레딧의 원화 환산은 플랜 가격을 확인하지 않아 적지 않는다.

| 항목 | 수량 | 단가(크레딧) | 합계 |
|---|---|---|---|
| 라운드 1 시트 | 4 | 견적 4.5 (묶음) | 4.5 |
| 라운드 2 편집 (GPT Image 2.5 Flare) | 8 | 0.25~1 | 2~8 |
| MASTER 4방향 (Seedream 5.0 Pro 또는 GPT Image) | 4 | 1~2.5 | 4~10 |
| 시험 컷 (Element 사용) | 6 | 0.25~1 | 1.5~6 |
| 시험 영상 (Seedance 2.0 Mini) | 1 | 5 | 5 |
| Element 생성 | 1 | **미확인** | ? |
| **합계** | | | **약 17~34 + Element** |

잔액 145.53 의 12~23%. 실제 차감은 생성 전후 `transactions` 차이로 기록한다.
Soul 학습, Marketing Studio, ComfyUI GPU 는 견적이 없어 넣지 않았다. 평가기는 CPU 만 써서 추가 비용이 없다.

## 9. SECURITY / RIGHTS REVIEW

| # | 위험 | 등급 | 조치 |
|---|---|---|---|
| R-1 | 계정의 기존 생성물 2건(`55c6bd2c…`, `f832e2a3…`)이 실존 연예인(Andy Lau) 초상을 주인공으로 둔 포스터 편집 | 높음 | 상업 게시 전 초상 사용 허락 확인. M40 참조·학습에 쓰지 않는다 |
| R-2 | 참조 3장이 실존 인물일 가능성 ("연예인 혼합" 언급) | 높음 | 얼굴 입력 금지(스키마 강제), 속성만 글로. 결과가 특정인과 닮았는지 사람 검토(`likeness_risk`) |
| R-3 | 오픈소스 정체성 부품의 insightface 비상업 모델 | 높음 | 생성에 쓰지 않음. 평가도 OpenCV SFace 만 |
| R-4 | Higgsfield 생성물의 상업 이용 범위와 Starter 플랜 조건 | 중간 | **미확인.** Higgsfield 약관·플랜 원문을 읽고 기록하기 전에는 상업 게시 HOLD |
| R-5 | 얼굴 특징 벡터는 생체 정보에 가까움 | 중간 | 평가기가 기본으로 벡터를 남기지 않음(시험으로 확인). 이미지·벡터는 공개 GitHub 에 두지 않음 |
| R-6 | 이 저장소는 공개 자료방 | 중간 | 생성 ID, 해시, 점수만 커밋. 이미지 원본은 비공개 버킷 |
| R-7 | n8n RESULT INBOX 무인증 | 중간 | 공유 비밀 헤더 또는 HMAC 추가 전 외부 AI 에 주소를 주지 않는다 |
| R-8 | SOPHIE / F30 덮어쓰기 | 중간 | Element 는 읽기만. 새 캐릭터는 새 ID. 평가기 `protected` 로 얼굴 겹침 차단 |
| R-9 | 자동차 브랜드 로고·차명 | 중간 | 브랜드 허락 없는 로고 노출 금지. 무브랜드 차량 또는 제휴 확인 후 |
| R-10 | 비용 폭주 | 낮음 | 생성은 견적 → 사람 승인 → 상한 크레딧 순. 스키마가 승인 없는 생성 상태를 막음 |
| R-11 | 평가 점수를 판정으로 오해 | 낮음 | 점수는 보조. calibrated=false 표시. LOCK 은 사람만 |

## 10. TEST PLAN

| ID | 시험 | 상태 |
|---|---|---|
| T-1 | 평가기 단위·기계 동작 11개 (해시 검증, 얼굴 없음, 변형 불변, 다른 사람 분리, 보호 대상 차단, 작은 얼굴 거절, 벡터 미보존) | **PASS** |
| T-2 | 스키마 규칙 6개 | **PASS** |
| T-3 | 보정: SOPHIE MASTER 1장 vs SOPHIE 생성 9장(양성), 다른 가상 인물 4장(음성). 양성 최솟값과 음성 최댓값 사이에 `same_pass` 를 둔다. 둘이 겹치면 Element 방식의 일관성 부족으로 판정 | **HOLD** (미디어 도메인 403) |
| T-4 | Higgsfield 읽기·견적 | **PASS** (크레딧 0) |
| T-5 | 승인된 라운드 1: 4장 생성 → generation_id 4개 → 평가 → 실제 차감 = 견적 확인 | HOLD (승인 필요) |
| T-6 | LOCK 흐름: 사람 승인 없이 잠기지 않음, 잠근 뒤 수정 불가, 새 버전 supersedes | 스키마 수준 PASS, UI 수준 HOLD |
| T-7 | n8n 반환: 같은 JOB_ID 수신 → 원장 → 재조회, 중복 차단 | HOLD (인증 추가 후) |
| T-8 | DVCC Studio 탭 수용 시험: 패널 6개, 비교 선택, LOCK 잠김 조건 | HOLD (기존 앱·저장소 접근 필요) |

## 11. EVIDENCE REQUIREMENTS

단계를 PASS 로 올리려면 다음이 모두 있어야 한다. 없으면 HOLD.

| 판정 | 필요한 증거 |
|---|---|
| DESIGN PASS | 이 문서, 스키마, 커밋 SHA |
| API_READ PASS | 도구 이름, 호출 시각, 응답 원문 일부, 크레딧 0 |
| QUOTE PASS | prepare 파라미터 전체, `credits`, `submitted:false` |
| GENERATED | 승인자·시각, generation_id(작업 ID), 모델, 시드, 생성 전후 `transactions` 차이, 결과 sha256 |
| EVALUATED | 평가 JSON (엔진 버전, 모델 해시, policy, 후보별 점수와 verdict) |
| LOCKED | `master_lock` 문서가 스키마를 통과, 사람 승인, 권리 체크 4개 |
| HIGGSFIELD INTEGRATION PASS | LOCK 이미지로 만든 element_id(또는 soul_id) + 그 ID 로 만든 실제 생성 1건의 generation_id + 평가 PASS. **견적이나 읽기만으로는 PASS 아님** |
| DVCC INTEGRATED | 기존 Replit 앱 ID, 화면 녹화 또는 스크린샷, API 응답 로그, 같은 JOB_ID 의 n8n 원장 재조회 |

공개 저장소에는 ID·해시·점수만 올린다. 이미지와 얼굴 벡터는 올리지 않는다.
