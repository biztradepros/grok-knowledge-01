RESPONDENT: CLAUDE — SYSTEM ARCHITECTURE & CRITICAL REVIEWER

---
id: draft-dream-lot-002-claude
lot: LOT-002 — DREAM DATA FACTORY RUNTIME / SHARED KERNEL / COMPUTABLE DEVELOPMENT REVIEW
report_to: ROOM-21 — DREAM RESEARCH OPERATIONS
ledger_message: LOT002-M004 (CLAUDE → ROOM21, RESULT)
status: draft
researched_on: 2026-10-06
sensitivity: none
---

# LOT-002 — Runtime 책임경계 · Shared Kernel · Computable Development

## 0. 읽는 법

### 표기 규칙

| 태그 | 뜻 |
|---|---|
| **FACT** | 이번 연구에서 코드·DB로 직접 실행해 확인했거나, 공식 문서에 근거한 사실 |
| **LIVE_EVIDENCE** | DREAM의 실제 Make·n8n·AI 통신 실측 결과. **이 보고서에는 0건이다.** 나는 DREAM의 라이브 시스템에 접근하지 않았다 |
| **INFERENCE** | 근거들로부터 추론한 판단 |
| **ASSUMPTION** | 검증되지 않은 가정 |
| **PROPOSAL** | 제안하는 설계 |
| **NOT_MEASURED** | 측정이 필요한데 아직 측정되지 않은 것 |

### 동봉 증거: `kernel/`

- `ledger.sql`: Message Ledger, Job, Outbox, Wait, Provider Session, Calc 메타데이터를 담은 커널.
- `failure_tests.sql`: §14 장애 10종 시뮬레이션.
- `run.sh`: PostgreSQL 16을 임시로 띄워 위 둘을 실행하는 스크립트.

**결과: 10/10 PASS (FACT, 커널 시뮬레이션).**

주의: 이 테스트는 **커널이 지켜야 할 규칙**을 증명한다. Make나 n8n 자체의 동작을 증명하지 않는다. 그 부분은 ROOM-22의 LIVE TEST 대상이다(`ROOM22-LIVE-TEST-CARDS.md`).

### LOT-001 정정

내 LOT-001 결론("Make는 가장자리로 유지, n8n은 미도입, Durable 엔진 중심")은 이번 보고서에서 **HOLD로 내린다**. 이유는 §3에 적었다.

---

## 1. Executive Conclusion

1. **Canonical State는 Runtime이 아니라 Kernel이 소유해야 한다.** Kernel = Supabase/Postgres 위의 Job + Message Ledger + Event/Outbox + Wait. 이 조건만 지켜지면 Make, n8n, Durable 엔진은 **교체 가능한 실행기(Adapter)**가 된다. Runtime 선택은 되돌릴 수 있는 결정이 되므로, **실측으로 고르면 된다.** (PROPOSAL, 근거: 커널 시뮬레이션 10/10 FACT)
2. **Make + n8n 병행은 그 자체로 Split-Brain이 아니다.** 아래 다섯 규칙(R1–R5)을 지키면 실행만 둘로 나뉠 뿐 상태는 하나다. 남는 비용은 **운영 복잡도**(콘솔·인증정보·모니터링이 2벌)이고, 이건 측정할 수 있다. (INFERENCE + FACT: F01, F03에서 Make 시뮬레이션 어댑터와 n8n 시뮬레이션 어댑터가 같은 outbox를 이중 처리 없이 나눠 처리함)

   | 규칙 | 내용 |
   |---|---|
   | **R1** | 어댑터는 테이블에 직접 쓰지 않는다. 커널 함수만 호출한다 |
   | **R2** | 모든 호출에 idempotency key를 붙인다 |
   | **R3** | 모든 응답·재개에 fencing token(job version)을 붙인다 |
   | **R4** | 어댑터는 업무 상태를 보관하지 않는다 |
   | **R5** | 재시도는 커널이 소유한다 |

3. **MVP에 Durable 엔진(Inngest·Temporal·Trigger.dev)은 필수가 아니다.** 커널의 Outbox + Sweep + Wait + fencing이 메시지 단위 내구성을 준다. 몇 분 걸리는 AI 리서치, 며칠 걸리는 사람 승인, 중복 없는 재시도, 같은 Job 복구가 모두 시뮬레이션에서 통과했다(FACT). Durable 엔진은 **"코드로 된 다단계 파이프라인이 늘어날 때"** 도입 여부를 TEST로 판단한다.
4. **Shared Kernel은 "대화와 결정의 문법"이다. "도메인 데이터"가 아니다.** 공유하는 것은 다음이다.
   - PROJECT, JOB, CONTEXT, MESSAGE, CLAIM, EVIDENCE, PARAMETER(인식 상태가 붙은 숫자), CALC_RUN 봉투, DECISION, APPROVAL/HUMAN_GATE, ARTIFACT, EVENT, DEPENDENCY 구조, ROLE

   공유하지 않는 것은 Floor, SKU, Order, Lookbook 같은 도메인 데이터다. 특히 Order처럼 대량 거래 데이터는 커널에 넣지 않는다. 커머스 플랫폼이 원본이고, 커널은 포인터와 이벤트만 갖는다.
5. **판정 요약**

   | 대상 | 판정 | 범위 |
   |---|---|---|
   | Supabase Kernel / Ledger | **KEEP** | Canonical State |
   | Make | **KEEP** | SEND, SaaS 연결, 알림, AI 디스패치 어댑터 |
   | Make | **LIMIT** | 라우팅 결정·상태 저장 금지 |
   | n8n | **TEST** | WAIT·타이머·대체 디스패처. 재개 시 fencing 준수 여부 |
   | Make + n8n 병행 | **TEST** | R1–R5 준수 + 운영비 실측 |
   | Inngest / Trigger.dev | **TEST** | PRODUCTION LATER 후보 |
   | Temporal | **REJECT (MVP)** | 포트폴리오 규모가 되면 재검토 |
   | Code-only 전면 전환 | **REJECT (MVP)** | 커널 함수와 계산 엔진만 코드로 |
   | 역할 정책 라우터 | **KEEP(신규)** | 커널 테이블 |
   | 게이트웨이 제품 | **TEST** | |

---

## 2. LOT-001에서 동의하는 부분

- **DB = 기억, Deterministic Engine = 계산, AI = Research/Review/Challenge, Human = FIXED 승인, Frontend = Decision Interface.** CONSENSUS_CANDIDATE로 등록하는 데 동의한다.
- Scenario, Evidence, Version, CalcRun은 명시적 객체여야 한다. LOT-001 프로토타입의 `input_hash`, `engine_version`, FIXED 트리거, `[[node_id]]` 숫자 자리표시자는 그대로 유효하다(FACT, LOT-001 테스트).
- BIM과 3D는 MVP를 지배하면 안 된다.

## 3. LOT-001에서 반대하는 부분 (내 결론 포함)

| LOT-001 주장 | 반대 이유 | LOT-002 처리 |
|---|---|---|
| (Claude) "n8n 미도입, Make 하나만, Durable 엔진이 상태 소유" | DREAM의 기존 자산(Make Remote, n8n Return/WAIT 연구)과 실측을 고려하지 않은 판단이었다. 상태를 커널이 소유하면 어떤 Runtime을 쓰든 바꿀 수 있으므로, 미리 제거할 이유가 없다 | **HOLD** → §6 책임 매트릭스와 ROOM-22 TEST로 대체 |
| (Claude) `ai_job`을 별도 테이블로 | AI 작업은 Job의 한 종류다. 별도 테이블은 대화(MESSAGE)와 작업 상태를 두 군데로 나눈다 | Kernel에서 **JOB + MESSAGE로 합침** |
| (공통) Workflow Engine이 업무 상태를 갖는 구조 | 엔진이 바뀌면 기억도 함께 잃는다 | 엔진은 실행 상태만 갖고, 업무 상태는 Ledger로 |
| (Gemini 요약본) n8n 단일화 / (Grok 요약본) Inngest 중심 | 원문을 보지 못했다. ROOM-21의 요약만 근거로 쓴다. 두 주장 모두 실측 없이 Runtime을 확정한다는 점에서 내 LOT-001과 같은 문제가 있다 | ARCHITECTURE_CONFLICT → TEST |
| (공통) ROOM 개념 부재 | DREAM은 ROOM 단위로 운영한다. ROOM은 작업의 **속성**이어야 한다. 정체성(ID)이 되면 방을 옮길 때 작업이 끊긴다 | F06 PASS (FACT) |

---

## 4. Shared Kernel

### 4.1 판정표

| 후보 | 판정 | 근거 / 형태 (PROPOSAL) |
|---|---|---|
| PROJECT | **SHARED** | `k_project(vertical)`. 대흥동, RADAR, 상품운영 모두 같은 형태 |
| JOB | **SHARED** | 상태기계 + `version`(fencing token). AI 작업, 사람 작업, 연구 LOT 모두 Job이다 |
| CONTEXT | **SHARED** | 방이나 AI가 바뀌어도 이어지는 연구·대화 맥락 |
| MESSAGE | **SHARED** | Canonical Conversation Memory (§5) |
| CLAIM | **SHARED** | 메시지에서 추출한 주장 + 인식 태그(FACT/INFERENCE…) + evidence_id. ROOM-21의 EXTRACT가 이 객체를 만든다 |
| EVIDENCE | **SHARED** | 문서·견적·법령·Live Test 결과·AI 리서치. `reliability`, `issued_on` |
| PARAMETER (추가) | **SHARED** | FIXED/ASSUMPTION/OPTION은 건축 전용이 아니다. 상품 원가 가정, 콘텐츠 KPI 가정에도 똑같이 쓰인다 |
| DECISION | **SHARED** | 어떤 CalcRun과 Evidence를 보고 누가 결정했는가 |
| APPROVAL / HUMAN_GATE | **SHARED** | HUMAN_GATE = `APPROVAL_REQUEST` 메시지 + `k_wait` + 승인 레코드. 같은 개념을 객체 두 개로 만들지 않는다 |
| VERSION | **SHARED (메커니즘)** | append-only + superseded 규약은 공통. 무엇을 버전 관리할지는 도메인이 정한다 |
| ARTIFACT | **SHARED** | 보고서, 이미지, PDF, 룩북을 가리키는 포인터(`git:…@sha`, storage path) |
| CALC_RUN | **SHARED (봉투)** | `engine_version`, `input_hash`, `outputs`는 공통. **계산 엔진 자체는 Vertical별**(사업수지, 단위경제, 성과 지표) |
| AI_JOB | **SHARED, 단 별도 객체 아님** | JOB(kind=AI_*) + MESSAGE로 충분하다 |
| WORKFLOW_RUN | **SHARED (포인터만)** | `k_event.runtime_ref`. Runtime 상태의 사본을 만들지 않는다 |
| DEPENDENCY | **SHARED (구조)** | edge(source, target, relation). 노드의 의미(층 면적, SKU 원가)는 도메인이 정한다 |
| EVENT | **SHARED** | 이벤트 로그 겸 Outbox |
| ROLE (추가) | **SHARED** | 역할별 정책: 허용 도구, 출력 스키마, 모델 고정, 예산 |

### 4.2 Vertical 전용 Domain (공유 금지)

| Vertical | 전용 객체 예 | 커널과의 연결 |
|---|---|---|
| A. Content / Intelligence | RadarItem, Issue(MAG), Lookbook, Creator, Landing, MediaAsset, PerformanceSnapshot | RadarItem → EVIDENCE. MAG 발행 → JOB. Mother Review → MESSAGE(type=CHALLENGE/VERIFY) |
| B. Product Operations | Product, SKU, Supplier, Quote, PO, Order, Shipment, Refund | 원가 가정 → PARAMETER. 단위경제 → CALC_RUN. **Order/Shipment의 원본은 커머스·물류 시스템**이고 커널은 `ARTIFACT_POINTER`와 EVENT만 갖는다 (INFERENCE: 대량 거래를 대화 커널에 넣으면 커널이 OLTP 시스템이 된다) |
| C. Development | Floor, Space, Unit, MdOption, ParkingRule, PF Tranche, Contractor | LOT-001 `dev_*` 그대로. 층 스키마는 A·B에 노출하지 않는다 |

---

## 5. Message Ledger Architecture

| 질문 | 답 | 라벨 |
|---|---|---|
| 1. 정말 필요한가? | **필요하다.** AI 공급자의 thread와 메모리는 공급자 소유이고, 만료되고, 서로 볼 수 없다. Runtime이 여러 개면 "누가 무엇을 언제 말했나"의 유일한 원본이 따로 있어야 한다. 단 **범위는 '의미 있는 발화'**(REQUEST/CLAIM/CHALLENGE/RESULT/APPROVAL…)로 한정한다. Runtime의 매 단계 로그까지 넣지 않는다 | INFERENCE |
| 2. Postgres/Supabase가 적절한가? | **적절하다.** 유일 제약(idempotency)과 행 잠금(fencing), 트랜잭션 Outbox, `SKIP LOCKED` 동시 소비가 모두 기본 기능이다. 시뮬레이션에서 그대로 작동했다. 규모가 커지면 월 단위 파티션으로 나눈다 | FACT (시뮬레이션) / INFERENCE (규모) |
| 3. Event Store와의 차이 | **Ledger = 의미(누가 누구에게 무엇을 주장·요청했나), Event = 사실(상태가 바뀌었다, 디스패치가 나갔다).** 메시지 1건을 append하면 같은 트랜잭션에서 이벤트 0~2건이 생긴다 | PROPOSAL, FACT(구현) |
| 4. Job State와 같은 테이블? | **아니다.** Job은 현재 상태(가변, 버전 있음), Message는 이력(불변)이다. 둘은 **같은 트랜잭션**에서 갱신하고, Job 상태는 Ledger와 Event로 재구성할 수 있어야 한다. 완전한 이벤트 소싱(상태를 매번 재생해 계산)은 MVP에 과하다 | PROPOSAL |
| 5. Provider Thread ID 연결 | `k_provider_session(job_id, provider, thread_ref, status)` + `k_message.provider_ref`. **thread는 캐시**다. 잃어도 Job은 잃지 않는다 | FACT (F07) |
| 6. Context Capsule 생성 | **Ledger에서 컴파일한다.** 내용: Job 상태 + 최근 N개 APPLIED 메시지 + **답이 없는 CHALLENGE** + 관련 CalcRun·Evidence ID. 어떤 메시지 ID로 만들었는지 기록하므로 재현 가능하다. AI가 만든 요약을 넣을 경우 CLAIM으로 표시하고 원문 ID를 함께 둔다 | FACT (`k_rehydrate`) |
| 7. Thread가 죽었을 때 SAME JOB 복구 | 기존 thread를 LOST로 표시 → Capsule 생성 → 새 thread 개설 → **같은 job_id, 같은 parent_id 체인**으로 이어 답한다 | FACT (F07) |
| 8. Ledger가 Runtime보다 상위 Canonical인가? | **그렇다. 단 조건이 붙는다.** Runtime의 실행 상태(타이머, 재시도 카운터)는 Runtime이 갖되, **Runtime이 통째로 사라져도 Ledger + Wait + Outbox로 다시 구동(re-drive)할 수 있어야 한다.** 이것이 어떤 Runtime이든 통과해야 할 **채용 시험**이다 | PROPOSAL |

메시지 코드 예시(`LOT002-M001…M007`)는 `k_message.code`로 그대로 담긴다. 시뮬레이션 타임라인에 M002·M003·M005가 실제로 기록됐다(FACT).

---

## 6. Runtime Responsibility Matrix

"점수"가 아니라 **책임별 Best Owner**다. Owner는 그 책임의 **결정과 진실**을 갖는 쪽이고, Executor는 실제로 실행하는 쪽이다.

| 책임 | BEST OWNER | Executor (교체 가능) | 판정 · 근거 |
|---|---|---|---|
| SEND | Kernel(outbox 행) | **Make** (현재 자산) / n8n / code worker | Make **KEEP**. INFERENCE: 기존 연결과 SaaS 커넥터 폭이 강점 |
| ROUTE (누구에게) | **Kernel ROLE 정책** | Make Router는 전달만 | Make **LIMIT**: 라우팅 *결정*을 Make 필터에 두면 정책이 두 군데 생긴다 |
| WAIT | **Kernel `k_wait`** (마감시한 + fence) | n8n Wait (TEST) / sweep 스케줄러 | n8n **TEST**: n8n Wait가 실행을 보관해도, 진실은 `k_wait` |
| RESUME | Kernel (메시지 append → 상태 전이) | n8n resume URL / webhook / code | fencing 필수 (FACT F08) |
| RETRY (전송) | Executor 내장 재시도 + **idempotency key** | Make/n8n 오류 핸들러 | 두 겹 재시도도 key 하나로 중복이 없다 (FACT F03) |
| RETRY (업무: 다시 묻기, 대체 공급자) | **Kernel `k_sweep`** | 아무 어댑터 | FACT F01 (3회 후 escalate) |
| QUESTION / ANSWER | Kernel Ledger | 어떤 채널이든 (API, 웹훅, 수동 붙여넣기 폼) | 수동 붙여넣기도 Ledger에 쓴다 → "복붙 0회"로 가는 경로 |
| HUMAN APPROVAL | Kernel (APPROVAL_REQUEST + wait + 승인) | DREAM CONTROL UI, Make 알림 | 늦은 답은 저장하되 실행하지 않는다 (FACT F08) |
| SAME JOB RECOVERY | **Kernel** (`k_rehydrate`) | 모든 AI 어댑터 | FACT F07 |
| LONG RUN (AI 수 분) | Kernel(job 상태 WAITING_AI) | **비동기 콜백**: Make가 요청만 보내고 끝나면 결과는 웹훅으로 받는다 | Make 시나리오 실행 상한 40분(+5분 유예) (FACT, 공식 커뮤니티 문서). 동기 대기에 의존하지 않는다 |
| WEBHOOK (수신) | Kernel 수신 함수 (서명 검증 → `k_append_message`) | Make/n8n 웹훅 허용. 단 **첫 동작이 Ledger 쓰기** | LIMIT |
| SAAS CONNECTOR | Make | (대안 n8n) | **KEEP** |
| AI DISPATCH | Kernel(무엇을, 어떤 역할로, 어떤 Capsule로) | Make HTTP/AI 모듈 (현재), code gateway (구조화 출력 역할) | **TEST**: 같은 역할을 두 경로로 보내 실패율·지연·비용 비교 |
| MESSAGE LEDGER WRITE | **Kernel 함수만** | 어댑터는 함수 호출만 | R1 |
| CALCULATION | **Calc Engine (code)** | — | Make/n8n/AI 안에서 계산하는 것은 **REJECT** (LOT-001 합의) |
| EVENT | Kernel `k_event` | — | |
| OBSERVABILITY | **Kernel 타임라인** (Ledger + Event + runtime_ref) | Runtime 자체 로그는 보조 | FACT (타임라인 질의) |
| FAILURE RECOVERY | **Kernel `k_sweep` + escalation** | 아무 어댑터 | FACT F01, F04, F08 |

### 후보 A–H 정리

| 후보 | 판정 | 한 줄 |
|---|---|---|
| A. Make only | **LIMIT** | 디스패치·SaaS 연결에는 강하다. WAIT·장기 실행은 40분 상한 때문에 커널이 대신 맡아야 한다 |
| B. n8n only | **TEST** | Wait/Resume이 강점이다. Make 자산의 이전 비용은 NOT_MEASURED |
| C. Make + n8n | **TEST** | R1–R5 준수 시 상태는 하나. 운영비 실측 필요 |
| D. Code only | **REJECT (MVP)** | 커넥터를 전부 다시 짜는 비용이 크다. 커널과 계산만 코드로 |
| E. Inngest | **TEST (later)** | §8 |
| F. Temporal | **REJECT (MVP)** | 운영 부담 대비 현재 규모에 과하다 (INFERENCE) |
| G. Trigger.dev | **TEST (later)** | E와 같은 등급의 대안 |
| H. Hybrid (Kernel + 교체 가능한 어댑터) | **PROPOSAL** | 이 보고서의 권고 구조 |

---

## 7. Make + n8n 재검증 — "정말 Split-Brain인가?"

**정의:** Split-Brain은 두 시스템이 **같은 사실에 대해 각자 진실을 갖고**, 서로 다르게 행동하는 상태다.

| 조건 | Split-Brain? | 근거 |
|---|---|---|
| Make Data Store와 n8n Static Data에 각각 job 상태가 있다 | **예** | 두 진실이 생긴다 |
| 둘 다 Ledger에 쓰지만, 직접 INSERT하고 idempotency가 없다 | **부분적** (중복 결과) | F03, F05 같은 상황에서 결과가 두 번 기록된다 |
| **Kernel = Canonical, 어댑터는 함수만 호출 (R1–R5)** | **아니다** | 시뮬레이션에서 Make 어댑터가 claim → 실패 → sweep → n8n 어댑터가 같은 행을 이어받음 → 결과 1건, `SKIP LOCKED`로 동시 claim 없음 (FACT F01·F03) |

**그래도 남는 위험 4가지 (INFERENCE)**

1. **숨은 상태:** n8n Wait로 멈춰 있는 실행은 실제로 상태를 갖고 있다. 커널에서 Job이 이미 취소·변경됐는데 n8n이 나중에 재개하면 낡은 행동을 할 수 있다.
   - 대응: 모든 재개는 fence를 제시해야 한다. 낡은 fence는 STALE로 저장만 된다(F08 FACT).
   - LIVE TEST에서 n8n이 실제로 fence를 전달하는지 확인해야 한다(NOT_MEASURED).
2. **정책 이중화:** 라우팅 조건이 Make Router 필터와 n8n IF 노드 양쪽에 생긴다.
   - 대응: 라우팅 결정은 커널 ROLE 정책에 둔다. 어댑터에는 "event type → 어댑터" 매핑만 둔다.
3. **이중 재시도 폭주:** Make 재시도 + n8n 재시도 + 커널 sweep이 겹친다.
   - 대응: 전송 재시도는 짧게, 업무 재시도는 커널만 한다. 각 재시도에 idempotency key를 쓴다.
4. **운영 비용:** 콘솔, 인증정보, 알림, 업그레이드가 2벌이다.
   - 이건 사실 판단이 아니라 **비용**이다 → ROOM-22에서 시간·장애·비용으로 측정한다.

**결론:** "Make + n8n = Split-Brain"은 **조건부 거짓**이다. 판정은 **TEST**다. 통과 기준은 ROOM-22 카드 T3, T4, T6이다.

---

## 8. Durable Runtime 비교

| 상황 | Kernel(Outbox+Sweep+Wait) | n8n | Make | Inngest / Trigger.dev | Temporal |
|---|---|---|---|---|---|
| AI 리서치 수 분 | ✓ 비동기 콜백 + WAITING_AI (FACT F01) | ✓ Wait/웹훅 | △ 40분 상한, 동기 대기 위험 (FACT 문서) | ✓ step 단위 | ✓ |
| 사람 승인 수 시간~수 일 | ✓ `k_wait` + 만료 escalate + 늦은 답 LATE (FACT F08) | ✓ resume URL. 재시작 후 생존 여부 NOT_MEASURED | ✗ 시나리오 분할 필요 | ✓ waitForEvent | ✓ signal |
| 외부 AI 질문·응답 | ✓ REQUEST/RESULT + provider_ref 중복 제거 (FACT F05) | ✓ | ✓ 전송 | ✓ | ✓ |
| 공급자 타임아웃 | ✓ 재큐 3회 → escalate (FACT F01) | ✓ 재시도 설정 | ✓ 오류 핸들러 | ✓ | ✓ |
| 같은 Job 재개 | ✓ Capsule (FACT F07) | △ 실행 단위로만 이어진다 | ✗ | △ 실행 단위로만 | △ |
| 중복 없는 재시도 | ✓ idempotency key (FACT F02·F03) | 노드 설계에 따라 다름 | 모듈 설계에 따라 다름 | ✓ step memoization | ✓ |
| 코드 다단계 + 보상(saga) | △ 직접 구현 | △ | ✗ | **✓** | **✓** |
| 운영 부담 | 낮음 (Postgres + 1분 스케줄러) | 중간 (셀프호스트 시) | 낮음 | 낮음 (SaaS) | 높음 |

**MVP NOW (PROPOSAL)**
- Kernel 내구성 + Make 어댑터 + n8n 시험 레인으로 간다.
- `k_sweep`은 1분 주기로 돈다. 스케줄러는 pg_cron, n8n cron, Vercel cron 중 무엇이든 된다. 스케줄러가 바뀌어도 커널은 그대로다.

**PRODUCTION LATER — Durable 엔진 도입 트리거 (사전 등록, 하나라도 충족 시 TEST 착수)**
1. **코드로 된 다단계 파이프라인**이 5개를 넘고, 단계 간 보상(취소 시 되돌리기)이 필요하다.
2. 커널 sweep으로 재구동한 Job 비율이 월 2%를 넘는다 (NOT_MEASURED).
3. 운영자가 Runtime 장애 복구에 주 2시간 넘게 쓴다 (NOT_MEASURED).

---

## 9. Computable Building Event Flow

공통 순서: **입력 변경 → (승인) → Parameter/Scenario 기록 → `calc.completed` → impact → 역할 Job → Ledger 대화 → Human Gate → Decision**

| 변경 | 쓰이는 객체 | 이벤트 | 소집 역할 (impact) | Human Gate |
|---|---|---|---|---|
| **Floor 면적 변경** (실측·설계 반영) | `change_request` → `approval` → `parameter_version`(새 행) | `param.changed` → `calc.completed` → `impact.computed` | 건축, 재무 | **필수** (입력값 변경. FIXED라면 근거까지) |
| **MD 변경** (3F: COMMERCIAL→KM36) | `scenario.selections` (OPTION, 승인 불필요한 탐색) | `scenario.changed` → `calc.completed`(BLOCK이면 멈춤) → `impact.computed` → `job.created`(kind=SCENARIO_REVIEW) | 의료, 법률, MEP/소방, 주차, 재무 (LOT-001 FACT) | 시나리오를 BASE로 승격할 때 |
| **B2 ↔ B3** | `scenario.overrides.basement.levels` (OPTION) | 위와 같음 + 정성 영향 edge(굴착·흙막이·지하수·인허가·공기) | 공사, 법률(인허가), 재무(금융기간) | BASE 승격 + 공기 변경 시 |
| **Medical 옵션** | 옵션 파라미터 (필요 면적, TI, 임대료) — 모두 ASSUMPTION | + `evidence.required` (의료시설 기준, 병상-면적 근거) | 의료, 법률, MEP/소방 | 옵션 파라미터를 근거와 함께 FIXED로 올릴 때 |
| **Retail 옵션** | 옵션 파라미터 | 표준 흐름 | 재무, (앵커 조건 시) 법률 | 임차 조건이 외부 발송될 때 |
| **LH / 민간 호수 변경** (55/77 → 다른 비율) | `units.lh`, `units.private` 파라미터 | `param.changed` → 수입·주차·BEP 재계산 + **외부 계약 영향** 이벤트 | 재무, 법률, LH 담당(사람) | **필수**: LH 협의 사항이다. AI·시나리오는 FIXED를 만들 수 없다 (LOT-001 FACT) |

모든 행에서 AI 결과는 `k_message`(RESULT/CHALLENGE)로 남는다. 숫자는 `[[node_id]]`로만 말한다(LOT-001 guard). 결정은 `k_decision.calc_run_id`로 근거 숫자에 고정된다. 엔진이 바뀌면 그 결정은 stale로 드러난다(FACT F09).

---

## 10. Frontend / DREAM CONTROL

| 화면 | 역할 | 데이터 | 구현 |
|---|---|---|---|
| BUILDING | 층 스택, 상태 색, 플래그 | Floor + 현재 CalcRun | **SVG** (LOT-001 합의). React Flow 아님 |
| SCENARIO | CalcRun N개 비교 | `calc_run` | 표 + Δ |
| FINANCE | KPI, 민감도 | `calc_run.outputs` | 차트 |
| FLOW | **계산 의존 DAG + 정성 영향 그래프** | `graph.edges()`, `dev_impact_edge` | **React Flow + ELK** |
| AI TALK | Job 하나의 대화 스레드 (parent_id 트리) | `k_message` | **타임라인/스레드 UI**. 그래프가 아니라 대화로 읽혀야 한다 |
| EVIDENCE | 파라미터·주장 → 근거 | PARAMETER, CLAIM, EVIDENCE | 표 + lineage 드로어 |
| APPROVAL | 승인 대기함 (Job, 마감, 늦은 답 포함) | `APPROVAL_REQUEST`, `k_wait`, LATE 메시지 | 카드 |
| OPERATIONS | outbox 건강도(대기·claim·dead), STALLED Job, 어댑터별 지연·실패 | `k_event`, `k_job` 집계 뷰 | 표 + 경보 |

- **React Flow는** FLOW 화면과, Job 하나에서 ROOM과 AI 사이 흐름을 보여주는 "토폴로지 미니맵"에만 쓴다 (PROPOSAL).
- **Next.js는 적절하다** (LOT-001 합의 유지).
- **Lovable은 LIMIT:** 화면 시안과, 읽기 전용 내부 화면(뷰 조회만)까지만 쓴다. Ledger 쓰기, 승인, 계산 경로에는 쓰지 않는다.
- **Realtime 구독은 ID만 받는다:**
  - 구독한다: 열려 있는 Job의 `k_job` 상태 변경, `k_message` insert(해당 job_id), 승인 대기 생성, `calc.completed`.
  - 구독하지 않는다: `k_event` 전체 스트림. OPERATIONS 화면은 집계 뷰를 주기적으로 조회한다. AI 토큰 스트리밍도 DB를 거치지 않는다.

---

## 11. AI TALK

**상태기계 (PROPOSAL; 메시지 유형과 상태 전이는 `ledger.sql`에 구현, FACT)**

```
REQUEST ─▶ (Researcher) CLAIM/RESULT ─▶ (Reviewer) VERIFY|CHALLENGE ─▶ (Researcher) RESPONSE
   ─▶ (Verifier) VERIFY 결과 ─▶ (Coach) COACH{CONTINUE|DEEPEN|CHALLENGE|VERIFY|REFRAME|STOP} ─▶ STOP
```

- **필수 키:** `job_id`, `context_id`(Job 경유), `message_id`, `parent_message_id`, 그리고 `idempotency_key`, `job_version_seen`, `provider_ref`. 이 셋도 키에 넣을 것을 제안한다.
- **종료 규칙:** CHALLENGE는 Job당 2라운드까지. 답이 없는 CHALLENGE가 남아 있으면 Coach는 STOP을 낼 수 없다(Capsule의 `open_challenges`로 확인).
- **공급자 메모리는 Canonical이 아니다.** 각 AI는 매 턴 Capsule을 받는다. thread는 캐시일 뿐이다(F07).
- **SRT TALK DOCK, MULTI-6 SAFE DOCK:** 정의를 보지 못했다(NOT_MEASURED). 이 둘이 메시지 유형과 수신자 집합(예: 6자 동시 질의)의 UI·프로토콜이라면, Ledger의 `type` + `recipient` + `parent_id`로 표현할 수 있다고 본다(ASSUMPTION). 정의를 주면 대응표를 만들겠다.

---

## 12. AI Gateway

| 선택지 | 독립성 | Fallback | 비용 추적 | 모델 고정 | 관측 | 도구·구조화 출력 | MCP | 공급자 thread 연속성 | 판정 |
|---|---|---|---|---|---|---|---|---|---|
| Direct APIs | 낮음 (SDK마다 다름) | 직접 구현 | 직접 | ✓ | 직접 | ✓ 최상 (공급자 기능 그대로) | 공급자별 | 공급자별 | **KEEP** (구조화 출력이 중요한 역할) |
| Vercel AI Gateway | 중간 (Vercel 종속) | ✓ | ✓ | ✓ | 2등급 (외부 연동) | ✓ | — | ✗ | **TEST** (Vercel에 올릴 경우) |
| LiteLLM | 높음 (OSS, 셀프호스트) | ✓ | ✓ | ✓ | 2등급 | ✓ (공급자 간 차이 있음) | — | ✗ | **TEST** |
| OpenRouter | 중간 (SaaS 경유) | ✓ | ✓ | ✓ | 2등급 | △ | — | ✗ | **LIMIT** (실험용. 민감 데이터 경로에는 쓰지 않음) |
| **Custom Role Router (커널)** | 최고 | 정책으로 | Ledger 기준 | **정책으로 고정** | Ledger 타임라인 | 위 경로에 위임 | 읽기 도구 MCP + `propose_change` | **Capsule로 해결** | **KEEP (신규 구축)** |

- 게이트웨이 비교 근거는 [SOURCE: mcp.directory 2026 비교](https://mcp.directory/blog/vercel-ai-gateway-vs-portkey-vs-openrouter-vs-litellm-2026) (FACT 수준은 2차 자료).
- **핵심:** 공급자 간 thread 연속성은 **어느 게이트웨이도 해결하지 않는다**. 그건 Ledger + Capsule의 일이다 (INFERENCE).
- **역할별 모델 정책 (PROPOSAL):**
  - `role → pinned model@version, fallback list, 금지 공급자(민감 데이터), 월 예산`을 둔다.
  - 모델 버전을 바꾸는 것은 **ENGINE_VERSION과 같은 승인 대상**이다.
  - "가장 싼 모델 자동 선택"은 쓰지 않는다. 분류·추출처럼 결과를 자동 검증할 수 있는 역할에만 비용 기반 선택을 허용한다.

---

## 13. Observability

**질문: DREAM CONTROL에서 Job 하나를 클릭하면 대화 + Runtime + 계산 + 근거를 한 Timeline으로 볼 수 있는가?**

→ **가능하다. 조건은 하나, Correlation 계약이다.**
- 모든 어댑터 호출에 `job_id`, `message_id`, `event_id`를 실어 보낸다 (Make 변수, n8n 필드, AI 요청 metadata).
- ack할 때 `runtime_ref`(Make 실행 ID, n8n execution ID)를 커널에 되돌려 쓴다.
- 시뮬레이션의 단일 UNION 질의가 메시지와 이벤트를 시간순으로 합치고, `n8n-exec-41` 같은 runtime_ref를 붙여 보여준다 (FACT).

| 도구 | 역할 | 판정 |
|---|---|---|
| **Custom DREAM Trace** (Ledger + Event + runtime_ref) | 업무 타임라인 = Canonical | **KEEP (구축)** |
| Workflow Runtime Trace (Make·n8n 실행 기록) | runtime_ref로 링크해서 들어가는 상세 | KEEP (링크만) |
| Provider Logs | 보조. 보존 기간이 제한되고 형식이 공급자마다 다르다 | LIMIT |
| Langfuse | 프롬프트, 토큰, 비용 수준의 LLM 트레이스 | TEST |
| OpenTelemetry | 서비스 간 지연·오류 스팬 | REPLACE LATER (운영 규모가 커질 때) |

---

## 14. Failure Simulation

`kernel/failure_tests.sql` 실행 결과 **10/10 PASS** (FACT, PostgreSQL 16, 커널 시뮬레이션). "LIVE 확인"은 ROOM-22 카드 번호다.

| # | 장애 | Canonical State | Retry Owner | Recovery Procedure | 시뮬레이션 | LIVE 확인 |
|---|---|---|---|---|---|---|
| F01 | AI 공급자 타임아웃 | `k_event`(claim 후 미ack), `k_job=WAITING_AI` | **Kernel `k_sweep`** | claim 시한 초과 → 재큐 (다른 어댑터도 가능) → 3회 후 `escalate.dispatch_failed` → notify 어댑터 | PASS | T5 |
| F02 | 웹훅 중복 | `k_message.idempotency_key` | 없음 (중복 흡수) | 같은 key면 기존 메시지 ID 반환 | PASS | T1 |
| F03 | Make 성공 + Ledger 쓰기 실패 | `k_event` 미ack 그대로 | **Kernel sweep** | 재구동 → 다른 어댑터가 같은 행 처리 → 결과 key `result:<event_id>` → 첫 결과 채택, 늦은 원본은 흡수 | PASS | **T2** |
| F04 | Ledger 성공 + AI 디스패치 실패 | `k_event` 미claim | Kernel(대기) / 아무 어댑터 | outbox에 남는다. 어댑터가 복구되면 처리 | PASS | T2 |
| F05 | AI가 RESULT를 두 번 반환 | `(job_id, provider_ref)` 유일 | 없음 | 두 번째는 첫 메시지 ID로 흡수 | PASS | T1 |
| F06 | ROOM 변경 | `k_job.room` + `room.changed` 이벤트 | — | Job ID 유지, 이력 보존 | PASS | — |
| F07 | AI thread 소실 | `k_message` + `k_provider_session` | Kernel `k_rehydrate` | 기존 thread LOST → Capsule(미답 CHALLENGE 포함) → 새 thread → 같은 parent 체인 | PASS | T8 |
| F08 | 사람이 3일 뒤 답함 | `k_wait`(마감) + `k_job.version` | Kernel sweep (만료 → STALLED) | 늦은 답은 **LATE로 저장, 자동 재개 안 함** → 현재 version으로 재확인 요청 → APPLIED | PASS | **T3, T4** |
| F09 | 계산 엔진 버전 변경 | `k_calc_run.engine_version`, `k_engine.active` | — | 과거 실행은 불변. 과거 엔진 기반 결정은 `k_stale_decisions`로 노출 → 재계산 Job | PASS | — |
| F10 | 옛 시나리오를 실수로 다시 엶 | `k_scenario.superseded_by` | — | 작업 시작 거부. 명시적 fork만 허용 | PASS | — |

---

## 15. MVP Architecture

```
            ┌──────────── DREAM CONTROL (Next.js) ────────────┐
            │ BUILDING · SCENARIO · FINANCE · FLOW · AI TALK  │
            │ EVIDENCE · APPROVAL · OPERATIONS                │
            └───────────────▲─────────────┬───────────────────┘
                 Realtime(ID)│             │ server actions
┌───────────────────────────┴─────────────▼─────────────────────────────┐
│ SUPABASE KERNEL (Canonical)                                           │
│ k_job · k_message(Ledger) · k_event(Outbox) · k_wait · k_provider_     │
│ session · ROLE 정책 · PARAMETER · CALC_RUN · DECISION · EVIDENCE       │
│ 함수: k_append_message · k_claim · k_ack · k_sweep · k_rehydrate        │
│ + Calc Engine(TS, LOT-001) · Vertical C 도메인(dev_*)                  │
└──────▲──────────────▲──────────────────▲──────────────────────────────┘
       │ claim/ack    │ claim/ack         │ append (웹훅 수신)
   ┌───┴────┐    ┌────┴─────┐       ┌─────┴──────────┐
   │ MAKE   │    │ n8n      │       │ Code worker    │
   │ KEEP   │    │ TEST lane│       │ (구조화 출력    │
   │ SEND·  │    │ WAIT·타이머│      │  AI 역할, 소수) │
   │ SaaS·  │    │ ·대체 디스 │      └────────────────┘
   │ 알림·AI │    │ 패치      │
   └────────┘    └──────────┘
```

---

## 16. Production Architecture

- **커널은 그대로 둔다.** 이것이 요점이다.
- Ledger를 월 단위 파티션으로 나누고, Vertical별 RLS, 역할별 공급자 정책 승인 흐름을 둔다.
- 어댑터 계층에서 ROOM-22 실측 결과로 KEEP·LIMIT·REPLACE를 확정한다.
- §8 트리거가 충족되면, **코드 다단계 파이프라인에 한해** Durable 엔진 1개를 어댑터로 추가한다. 이 엔진도 R1–R5를 지켜야 한다.
- Vertical A·B 도메인 팩을 추가한다. Order와 Shipment는 외부 시스템이 원본이고 커널은 포인터만 갖는다.
- 관측: Custom Trace + Langfuse(TEST 통과 시) + OpenTelemetry(규모가 커질 때).

---

## 17. Migration Path (기존 자산 보존, 단계마다 되돌릴 수 있음)

| 단계 | 내용 | 되돌리기 |
|---|---|---|
| **0. Shadow** | 기존 Make 시나리오, n8n Return/WAIT, GPT↔Gemini/Grok 실험 흐름은 그대로 둔다. 각 흐름의 **첫 모듈과 마지막 모듈에 `k_append_message` 호출만 추가**한다. 동작은 바꾸지 않고 Ledger만 채운다 | 호출 모듈 삭제 |
| **1. Ledger를 읽기 원본으로** | DREAM CONTROL의 AI TALK와 OPERATIONS가 Ledger만 읽는다. ROOM-21 합성도 Ledger 메시지에서 시작한다 | UI만 교체 |
| **2. Outbox 전환** | 새 요청은 `REQUEST` append → outbox → Make가 `k_claim`으로 가져간다 (push 대신 pull) | Make 직접 트리거로 복귀 |
| **3. WAIT 실측** | 같은 승인 흐름을 (a) n8n Wait, (b) 커널 `k_wait` + sweep 두 경로로 2주간 운영하고 T3·T4 결과로 판정 | 패배한 경로를 끈다 |
| **4. 라우팅 정책 이관** | Make Router 조건을 커널 ROLE 정책으로 옮긴다. Make는 "event type → 전송"만 남긴다 | 조건 복원 |
| **5. (조건부) Durable 엔진** | §8 트리거 충족 시 TEST LOT | 어댑터 하나 제거 |

---

## 18. What NOT to build

1. 자체 메시지 브로커(Kafka 등)나 자체 워크플로 엔진. Outbox + Sweep 이상으로 만들지 않는다.
2. 완전한 이벤트 소싱(상태를 재생으로만 계산). 상태 테이블 + 로그로 충분하다.
3. 커널 안의 Order/Shipment/결제 원장.
4. AI 공급자 메모리나 thread에 의존하는 기능.
5. "가장 싼 모델 자동 선택" 라우터.
6. 라운드 상한 없는 AI끼리의 자유 대화.
7. Make 또는 n8n 안에서의 계산과 라우팅 결정.
8. Runtime별로 따로 만든 대시보드. 관측은 커널 타임라인 하나로 한다.
9. 범용 EAV 커널(모든 도메인을 key-value 하나로). 커널은 문법, 도메인은 타입이 있는 테이블.

---

## 19. Final Recommendation

> DREAM이 AI를 바꾸고, ROOM을 바꾸고, Workflow Runtime을 바꾸더라도 JOB, MEMORY, EVIDENCE, CALCULATION, DECISION을 잃지 않으려면, **그 다섯 가지를 어떤 Runtime도 소유하지 않게 해야 한다.**

구체적으로 다음과 같다.

1. **Supabase Kernel**(Job + Message Ledger + Outbox + Wait + Parameter/CalcRun/Decision/Evidence)을 Canonical State로 둔다. **KEEP** (CONSENSUS_CANDIDATE 확장)
2. **어댑터 계약 R1–R5**를 모든 Runtime의 채용 시험으로 쓴다. 통과하는 Runtime은 무엇이든 KEEP 가능하다.
3. **Make는 KEEP**(SEND, SaaS 연결, 알림, AI 디스패치)이고 **LIMIT**(라우팅 결정·상태 저장 금지)이다. **n8n은 TEST**(WAIT, 대체 디스패치)다. **Make + n8n 병행은 TEST**다. 조건부로 Split-Brain이 아니다.
4. **Durable 엔진은 MVP에 넣지 않고**, 사전 등록한 트리거로 TEST한다. Temporal은 MVP 단계에서 REJECT한다.
5. **역할 정책 라우터**를 커널에 둔다. 게이트웨이 제품은 TEST다.
6. **대흥동 Computable Building**은 이 커널 위의 Vertical C 도메인 팩이다. 같은 커널로 Vertical A(Content), B(Product Ops)를 붙인다.

**ROOM-21에 올리는 분류 제안**

| 분류 | 항목 |
|---|---|
| CONSENSUS_CANDIDATE | LOT-001 합의 + "Canonical State = Kernel, Runtime = Adapter" (세 연구소의 독립 판단으로 검증 필요) |
| ARCHITECTURE_CONFLICT | n8n 단일 vs Make+n8n vs Durable 중심 → **TEST LOT 전환** |
| LIVE TEST REQUIRED | ROOM-22 카드 T1–T10 |
| ARCHITECTURE DECISION CANDIDATE | 어댑터 계약 R1–R5 채택, 커널 스키마 v0 채택 |
| NEXT LOT | LOT-003: ROOM-22 Runtime 실측 (Shadow 단계 + T1–T10) |

---

## 20. Questions / Unknowns

| # | 질문 | 왜 중요한가 | 라벨 |
|---|---|---|---|
| Q1 | 현재 Make 시나리오 수, 월 실행량, 실패율은? | KEEP·LIMIT 판단의 기준선 | NOT_MEASURED |
| Q2 | n8n은 클라우드인가 셀프호스트인가? 버전은? | Wait 실행의 재시작 생존, 운영비 | NOT_MEASURED |
| Q3 | GPT↔Gemini/Grok 실험의 전송 경로는 API인가, 채팅 UI(Custom GPT action, Manus 등)인가? | UI 경로는 idempotency key와 fence를 붙이기 어렵다 → 수동 붙여넣기 폼이 필요할 수 있다 | ASSUMPTION |
| Q4 | Make Remote connection이 사용자 지정 헤더나 필드(job_id, idempotency key)를 끝까지 전달하는가? | R2·R3 성립 여부 | NOT_MEASURED |
| Q5 | Supabase 플랜에서 pg_cron을 쓸 수 있는가? | sweep 스케줄러 선택 | NOT_MEASURED |
| Q6 | SRT TALK DOCK, MULTI-6 SAFE DOCK, DREAM ROOM의 정확한 정의 | Ledger 메시지 유형 대응 | NOT_MEASURED |
| Q7 | 사람 승인자는 누구이고, 승인 마감 SLA는? | `k_wait.deadline` 기본값, 에스컬레이션 대상 | ASSUMPTION |
| Q8 | PF 조건 등 민감 데이터를 보내면 안 되는 공급자 목록 | ROLE 정책의 금지 공급자 | NOT_MEASURED |
| Q9 | Vertical B의 커머스·물류 원본 시스템은? | 커널이 포인터만 갖는 경계 | NOT_MEASURED |

---

### 부록 — 증거 재현

```bash
# PostgreSQL 16 바이너리가 있는 리눅스, root로 실행 (내부에서 postgres 사용자로 임시 클러스터 기동)
drafts/dream-lot-002/kernel/run.sh /path/to/short/workdir
# 기대 출력: F01–F10 PASS + Job 타임라인 12행
```

### 부록 — 이번 실행 결과 원문 (요약)

```
F01 PASS provider timeout -> kernel retry x3 -> escalate (owner: k_sweep)
F02 PASS duplicate webhook -> 1 message (owner: ledger unique key)
F03 PASS adapter success + ledger write failure -> re-drive, first result wins (owner: k_sweep + idempotency key)
F04 PASS ledger ok + dispatch down -> outbox row waits, any adapter drains later (owner: outbox)
F05 PASS RESULT twice -> deduped by (job, provider_ref)
F06 PASS room change -> same JOB id, room is an attribute + event
F07 PASS thread lost -> capsule from ledger -> new thread, same JOB/parent chain
F08 PASS 3-day-late human answer -> kept as LATE, re-confirm required (owner: fencing token)
F09 PASS engine change -> old runs immutable, decisions flagged stale
F10 PASS superseded scenario -> blocked unless explicit fork
```

연구 중 발견한 결함 1건도 기록한다. 첫 실행에서 `k_claim`이 이벤트 유형을 구분하지 않았다. 그래서 AI 디스패처가 F01에서 생긴 escalate 행을 가져갔는데도 F03 단언이 통과했다. → 유형 필터를 추가하고 F03이 "GROK 디스패치"인지 단언하도록 고친 뒤 재실행해 PASS를 확인했다 (FACT). **교훈:** 어댑터는 자기 담당 이벤트 유형만 가져가야 한다. 이 규칙은 R1에 추가할 것을 제안한다.
