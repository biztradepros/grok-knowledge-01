RESPONDENT: CLAUDE — SYSTEM ARCHITECTURE & CRITICAL REVIEWER

---
id: draft-dream-lot-001
lot: LOT-001 — DAEHEUNG AI DEVELOPMENT COMPUTING RESEARCH
status: draft
source_ai: claude
researched_on: 2026-10-06
sensitivity: none
---

# DREAM AI Development Operating System — 대흥동 Computable Building 연구 보고서

**표기 규칙** — 중요한 주장마다 아래 태그를 붙인다.

| 태그 | 뜻 |
|---|---|
| **[FACT]** | 이 연구 중 직접 실행·검증한 사실, 또는 공식 문서·널리 확립된 사실 |
| **[SOURCE]** | 외부 출처에 근거 (링크는 본문과 맨 끝 Sources에 있다. 2차 보도가 섞여 있으니 계약·투자 판단 전에 원문을 다시 확인할 것) |
| **[INFERENCE]** | 근거들로부터 내가 추론한 판단 |
| **[ASSUMPTION]** | 검증되지 않은 가정. DREAM이 확인해야 한다 |

**동봉물** — `prototype/`: 실행되는 계산 엔진, 의존성 그래프, AI 숫자 가드, 테스트 10개, Postgres 스키마, AI·Workflow·API 계약서. 숫자는 전부 **DUMMY**다. 대흥동 실데이터가 아니다.

---

## 1. EXECUTIVE CONCLUSION

1. **방향은 맞다. 다만 지금 그리는 그림의 절반은 MVP에 필요 없다.** 핵심은 세 가지 장치다. **(a) 모든 입력 숫자의 출처·상태 장부(Parameter Ledger), (b) 결정론적 계산 엔진, (c) 변경 영향 그래프.** 이 셋이 없으면 Multi-AI도 화면도 "그럴듯한 숫자 생성기"가 된다. **[INFERENCE]**
2. **2026년 현재 가장 현실적인 구조** **[INFERENCE]**
   - **Frontend:** Next.js(React) + Vercel. Lovable은 1주짜리 화면 시안에만 쓰고 버린다.
   - **Backend/DB:** Supabase(Postgres + Realtime + Storage + pgvector) 하나. Graph DB와 BIM DB는 지금 쓰지 않는다.
   - **Calculation:** 브라우저와 서버가 **같은 TypeScript 계산 패키지**를 쓴다. 실행 결과는 입력 해시와 함께 DB에 저장한다.
   - **Workflow:** 코드 기반 Durable Workflow 엔진 **하나**(Inngest, Trigger.dev, Vercel Workflow 중 택1)가 상태·대기·승인을 맡는다. Make/n8n은 둘 중 **하나만**, 외부 SaaS 연결용 "가장자리"로 쓴다.
   - **Multi-AI:** UI는 역할(Role)만 알고, 공급자는 AI Gateway 뒤에 숨긴다. 여러 모델을 쓰는 건 **Challenger 단계에만** 투입한다.
3. **DREAM의 원칙 "AI는 숫자를 기억하지 않는다"는 옳지만 부족하다.** 다음 세 가지를 더해야 실제로 지켜진다 (§3). **[INFERENCE]**
   - AI는 숫자를 **쓸(commit) 수 없다**.
   - 화면은 **AI가 쓴 문장 속 숫자를 그대로 보여주지 않는다**.
   - 모든 숫자에는 **상태·근거·승인**이 붙는다.
   
   이 세 가지는 프로토타입에서 코드와 DB 제약으로 구현해 검증했다. **[FACT]**
4. **"Digital Twin"이라는 이름은 정확하지 않다.** Digital Twin Consortium의 정의는 실물과의 **동기화**를 요구한다 **[SOURCE]**. 지금 만드는 것은 **Development Decision Twin**이다. 실물 센서가 아니라 **결정·근거와 동기화되는 사업 모델**이라는 뜻이다. 제품명으로는 **Computable Building**이 좋다. **[INFERENCE]**
5. **시장 공백은 실재한다.** **[INFERENCE, §2 근거]**
   - TestFit, Forma, Giraffe, Archistar, Deepblocks는 매싱·수익성의 앞단까지만 다룬다.
   - Procore, ALICE, Togal은 시공·공정·물량 단계를 다룬다.
   - 아무도 다루지 않는 영역이 있다. "**층별 MD 옵션 ↔ 법정 주차 ↔ PF 금융비 ↔ LH·민간 혼합 수입 ↔ 근거 장부 ↔ 역할별 AI 검토**"를 한국 혼합용도 개발사업 하나에서 연결하는 것이다.
6. **30일 안에 가능한 것:** 층 클릭 → 옵션 선택 → 결정론적 재계산 → 영향 경로 → 필요한 역할만 AI 검토 → 사람 승인까지. 3D, BIM, 자동 모델 라우팅, AI끼리의 자유 토론은 MVP에서 뺀다 (§16).

---

## 2. CURRENT STATE OF THE ART (2025–2026)

### 2.1 분야별 지형

| 분야 | 대표 사례 | 구분 | 근거 |
|---|---|---|---|
| AI + 수익성(Feasibility) | TestFit — 매싱·주차·세대 구성·비용. 2026년 9월 외부 AI 어시스턴트가 TestFit 수익성 검토를 다룰 수 있게 열었다 | 상용 | [SOURCE](https://www.nomic.ai/compare/testfit-alternatives), [SOURCE](https://www.testfit.io/news/at-dallas-testfit-ai-assistants-can-now-guide-real-estate-feasibility-studies) |
| AI + 수익성 | Archistar(호주, 부지분석 + 생성설계), Giraffe(3D + 재무 통합), Deepblocks(미국 300개 이상 도시, 용도지역 → 최대 건축 → 프로포마) | 상용 | [SOURCE](https://www.feasly.com.au/guides/property-development-apps-digital-tools-australia), [SOURCE](https://landchecker.com.au/articles/landchecker-partner-with-3d-design-platform-giraffe/), [SOURCE](https://urbanland.uli.org/economy-markets-trends/ul-interview-a-deep-dive-on-deepblocks-bringing-demographic-data-to-pro-forma-modeling) |
| 생성설계 / 환경분석 | Autodesk Forma(옛 Spacemaker): 일조·바람·소음. 2026-09-15 AU에서 Forma 포함 3개 산업 클라우드에 에이전트형 AI를 미리 공개, 2027년부터 출시 예정 | 상용 | [SOURCE](https://www.nomic.ai/compare/testfit-alternatives), [SOURCE](https://macaubusiness.com/autodesk-advances-agentic-ai-in-its-three-industry-clouds/) |
| 공사 PM + 에이전트 | Procore Helix: Agent Builder(오픈 베타), RFI·일일보고 에이전트 (Groundbreak 2025) | 상용 | [SOURCE](https://www.businesswire.com/news/home/20251015796723/en/Procore-Advances-the-Future-of-Construction-with-New-AI-Innovations-at-Groundbreak-2025) |
| AI 공정 | ALICE Technologies: 최적화 엔진 + Schedule Insights Agent(2025 가을). nPlan: 과거 데이터로 공기 리스크 예측 | 상용 | [SOURCE](https://blog.alicetechnologies.com/alices-2025-annual-review) |
| AI 적산 | Togal.AI: 도면 물량 산출 자동화 (정확도·속도 수치는 회사 주장 위주) | 상용 | [SOURCE](https://www.capterra.com/p/10001876/Togal-AI/) |
| BIM 데이터 플랫폼 | Speckle: 오픈소스, 모델 데이터를 push/diff/branch. 2025년부터 자연어 질의(Speckle Intelligence) | 오픈소스 + 상용 | [SOURCE](https://aecmag.com/features/speckle-the-open-source-cloud-data-platform/) |
| LLM + BIM 연구 | Text2BIM(2024, 다중 에이전트 → BIM 코드 + 규칙 검사), BIMgent(2025), Sketch2BIM(2025) | 논문 | [SOURCE](https://arxiv.org/pdf/2510.20838) |
| Digital Twin + LLM / 다중 에이전트 | Graph-DT-GPT(그래프 기반 DT + 다중 에이전트 질의), LLM 다중 에이전트로 DT 시뮬레이션 파라미터 설정 | 논문 | [SOURCE](https://arxiv.org/pdf/2405.18092) |
| 오픈소스 목록 | Awesome-AECO (AEC 오픈소스 큐레이션) | GitHub | [SOURCE](https://github.com/osama-ata/Awesome-AECO) |
| 한국 | 스페이스워크 랜드북 등 AI 소형 개발 수익성 서비스가 있다고 알고 있다 | 상용 | **[ASSUMPTION]** 이번 조사에서 최신 상태 미확인 |

### 2.2 DREAM과 가장 비슷한 사례 TOP 10

| # | 사례 | WHAT EXISTS | WHAT WORKS | WHAT DOES NOT EXIST | DREAM이 차별화할 지점 |
|---|---|---|---|---|---|
| 1 | **TestFit** | 매싱 → 주차·세대·비용의 실시간 재계산. 외부 AI 연결 | "옵션 바꾸면 숫자가 바로 바뀐다" UX가 시장에서 검증됨 [INFERENCE] | 근거 장부, PF 금융, 한국 LH·용도별 주차 규칙, 역할별 AI 검토 | 숫자마다 FIXED/ASSUMPTION + 근거. 한국 혼합용도 규칙 |
| 2 | **Autodesk Forma + Assistant** | 환경분석 + 연결된 프로젝트 데이터 위의 에이전트 (2027 출시 예정) | 대형 생태계, BIM과의 연속성 | 사업수지·금융, MD 옵션 경제성 | 설계가 아니라 **사업 결정**이 단위 |
| 3 | **Giraffe** | 지도 + 3D + 재무 통합 | 부지 발굴 → 수익성 시간 단축 | 층별 MD·앵커 임차, 승인 흐름 | 단일 부지를 깊게 다루는 운영체제 |
| 4 | **Archistar** | 규제 기반 부지분석 + 생성설계 | 인허가 규칙을 계산 가능하게 만듦 | 한국 법규, 운영·승인 | 한국 법규 팩을 근거와 함께 |
| 5 | **Deepblocks** | 용도지역 → 최대 건축 → 프로포마 자동 | 대량 부지 스크리닝 | 개별 사업 운영, 전문가 협업 | 스크리닝이 아니라 실행 단계 |
| 6 | **Procore Helix / Agent Builder** | 공사 문서 위 노코드 에이전트 | 반복 문서 업무(RFI, 일일보고) 자동화 | 개발 초기 수익성, 시나리오 비교 | 시공 이전 단계의 결정 |
| 7 | **ALICE Technologies** | 공정 최적화 엔진 + 대화형 에이전트 | **"엔진이 계산하고 AI는 설명한다"** 패턴의 상용 성공 사례 [INFERENCE] | 비용·수익·MD | 같은 패턴을 사업수지 전체에 적용 |
| 8 | **Speckle** | 모델 데이터 버전관리(diff/branch) + 자연어 질의 | AEC 데이터를 "코드처럼" 관리 | 재무·결정 | 나중의 BIM 연결 통로 후보 |
| 9 | **Togal.AI** | 도면 → 물량·견적 자동 | 적산 시간 단축 | 사업 단위 의사결정 | 견적을 근거(Evidence)로 흡수 |
| 10 | **Graph-DT-GPT / Text2BIM 계열 연구** | 그래프 DT + LLM 다중 에이전트, 규칙 검사 반복 | 자연어 ↔ 구조화 모델 변환 가능성 입증 | 실무 운영, 승인, 재무 책임 | 연구 아이디어를 운영 규율과 결합 |

**종합 [INFERENCE]**
- 시장은 **앞단**(설계·수익성 스크리닝)과 **뒷단**(공사 운영)으로 나뉘어 있다.
- 그 사이에 비어 있는 단계가 있다. "**결정이 내려지고, 바뀌고, 근거가 쌓이는 개발 PM 단계**"다.
- DREAM의 기회는 여기에 있다. 이 단계에서는 AI 모델 성능이 아니라 **데이터 규율(장부·버전·승인)**이 해자(moat)가 된다.

---

## 3. DREAM CONCEPT VALIDATION

### 3.1 원칙 검증

> AI DOES NOT REMEMBER THE NUMBER. DATABASE REMEMBERS THE NUMBER. CALCULATION ENGINE CALCULATES THE NUMBER. AI RESEARCHES, REVIEWS AND EXPLAINS THE NUMBER.

**동의한다. 하지만 이 문장만으로는 깨진다.** 실제로 깨지는 경로는 다섯 가지다. **[INFERENCE]**

1. AI가 설명문에 숫자를 직접 써 넣는다. 사람은 그 숫자를 복사해 보고서에 쓴다. → 원칙이 화면에서 깨진다.
2. AI가 "공사비 평당 ○○ 가정"을 제안하고, 누군가 그 값을 엑셀에 붙인다. → 출처 없는 숫자가 장부에 들어간다.
3. 계산식이 바뀌었는데 예전 결과와 섞인다. → 같은 시나리오에 숫자가 두 개 생긴다.
4. 가정값(ASSUMPTION)이 시간이 지나며 확정값(FIXED)처럼 취급된다. → 가장 흔하고 가장 비싼 오류다.
5. 시나리오 복사본이 원본을 덮어쓴다.

### 3.2 개선된 원칙 (DREAM NUMBER CONTRACT)

| # | 원칙 | 구현 (프로토타입에서 검증) |
|---|---|---|
| 1 | 입력 숫자는 **Parameter 장부에만** 산다 | `core_parameter_version` 테이블 하나. 산출값(DERIVED)은 입력으로 저장할 수 없다 — enum에서 아예 뺐다 **[FACT]** |
| 2 | 산출 숫자는 **CalcRun에만** 산다 | `core_calc_run`에 `(engine_version, input_hash)` 유일키 **[FACT]** |
| 3 | 같은 입력 + 같은 엔진 = 같은 출력 + 같은 해시 | 결정론 테스트 통과 **[FACT]** |
| 4 | **FIXED는 승인 + 근거가 있어야 한다** | DB 트리거: 승인 없는 FIXED 입력이 실제로 거부됨(PostgreSQL 16) **[FACT]** |
| 5 | 시나리오는 FIXED를 만들 수 없다 | 엔진 예외 + DB CHECK 제약, 둘 다 실제로 거부됨 **[FACT]** |
| 6 | **AI는 제안만 하고 커밋하지 않는다** | AI 출력은 `change_request`(FIXED 제안 금지)로만 나간다. AI 서비스 계정은 parameter 쓰기 권한이 없다(RLS 설계) |
| 7 | **화면은 AI가 쓴 숫자를 그대로 보여주지 않는다** | AI는 `[[profit]]` 같은 자리표시자로만 숫자를 말한다. 날것의 "999.9억"은 계산 결과와 대조해 거부한다(guard 테스트 통과) **[FACT]** |
| 8 | 모든 AI 주장은 FACT/SOURCE/INFERENCE/ASSUMPTION 중 하나 + evidence_id | AI Job 계약서의 출력 스키마로 강제 |

---

## 4. FRONTEND RECOMMENDATION

### 4.1 비교 (5점 만점, 대흥동 기준) **[INFERENCE]** — 개별 사실은 표 아래 근거

| 기준 | Lovable | Next.js/React + Vercel | Supabase 직결 SPA | Replit | Custom React (Vite) |
|---|---|---|---|---|---|
| 개발속도 (첫 화면) | **5** | 3 | 4 | 4 | 3 |
| 유지보수 (6개월 후) | 2 | **5** | 3 | 2 | 4 |
| 실시간성 | 3 | **4** | 4 | 3 | 4 |
| AI 스트리밍 | 3 | **5** (AI SDK, 라우트 핸들러) | 2 (Edge Function 필요) | 3 | 4 |
| 그래프 시각화 | 3 | **5** (React Flow) | 4 | 3 | 5 |
| 계산 (공유 TS 패키지) | 2 | **5** | 3 | 3 | 4 |
| Supabase 연결 | 5 | 5 | 5 | 4 | 5 |
| Make/n8n 연결 | 3 | **5** (서명된 웹훅 핸들러) | 2 | 3 | 3 |
| Multi-AI 연결 | 2 | **5** (게이트웨이를 서버에서) | 2 | 3 | 4 |
| 버전관리 | 2 (한 브랜치 동기화, 기존 저장소 가져오기 불가) | **5** | 4 | 3 | 5 |
| 확장성 | 2 | **5** | 3 | 2 | 4 |
| 비용 (초기) | 4 | 4 | 5 | 4 | 4 |

- Lovable의 한계 **[SOURCE](https://rapidevelopers.com/lovable-issues/lovable-limitations-and-production-readiness)**
  - GitHub 동기화는 한 번에 한 브랜치만 되고, 기존 저장소를 가져올 수 없다.
  - Lovable Cloud에서는 SQL 에디터와 service role 키를 쓸 수 없다.
  - 2026년 7월 Cloud 내보내기 기능이 생겼다.
- React Flow(@xyflow/react)는 노드 기반 UI의 사실상 표준이다. dagre/ELK 레이아웃과 함께 쓴다 **[SOURCE](https://landscape.jimmysong.io/projects/xyflow/)**.

### 4.2 추천

**Next.js(App Router) + Vercel + Supabase.** 화면 구성은 다음과 같다.

| 화면 | 구현 |
|---|---|
| BUILDING VIEW | 커스텀 SVG 층 스택. 3D는 하지 않는다 |
| FLOOR VIEW | 사이드 패널 |
| SCENARIO VIEW | CalcRun N개 비교 표 |
| FLOW VIEW | React Flow + ELK |
| FINANCIAL VIEW | KPI + 토네이도 민감도 차트 |
| EVIDENCE VIEW | 파라미터 장부 표 + lineage |
| OPERATIONS VIEW | wf_run + 승인 대기 |
| AI COACH | SSE 스트리밍 패널 |

컴포넌트 트리와 CLICK 순서는 `prototype/apps/web/STRUCTURE.md`에 있다.

**Lovable은 1주차 화면 시안에만** 쓴다. 대표·MD 담당과 층 스택 UX를 합의하는 용도다. 코드는 가져오지 않는다. **[INFERENCE]** 계산 로직이 프롬프트로 생성된 UI 코드 안에 섞이면, 원칙 2·3이 깨진다.

---

## 5. BACKEND RECOMMENDATION

| 구성요소 | 선택 | 이유 |
|---|---|---|
| 주 DB | **Supabase Postgres** | 관계형 무결성(외래키·트리거·CHECK)이 "숫자 규율"의 핵심이다. Realtime, Storage, Auth, RLS가 한 곳에 있다 [INFERENCE] |
| 문서·근거 | Supabase Storage + `pgvector` 청크 | PDF·견적서·법령 원문 → 청크 → AI가 chunk_id로 인용 |
| 그래프 | **Postgres 테이블 + 앱 메모리 DAG** | 계산 노드는 수십~수백 개 수준이다. Graph DB는 운영 부담만 늘린다 [INFERENCE]. 노드가 수만 개가 되거나 포트폴리오 간 질의가 필요해지면 재검토 |
| Vector DB 별도 | **불필요** | 문서 수천 건 규모면 pgvector로 충분하다 [INFERENCE] |
| BIM DB | **지금 불필요** | §12 |
| 실시간 | Supabase Realtime **Broadcast**(id만 전송) → API로 재조회 | Postgres Changes는 payload 크기 제한(64바이트 초과 필드 생략)이 있다 **[SOURCE](https://supabase.com/docs/guides/realtime/limits.md)** |
| 서버 로직 | Next.js 라우트 핸들러 + Durable Workflow | Edge Function은 wall-clock 제한이 있다(546 에러) **[SOURCE](https://supabase.com/docs/guides/realtime/limits.md)**. 긴 AI 작업에는 맞지 않는다 |

---

## 6. DATABASE MODEL

전체 DDL은 `prototype/db/schema.sql`에 있다. PostgreSQL 16에서 적용을 검증했다 **[FACT]**.

### 6.1 구조

```
core_project ─┬─ core_model_version (불변 스냅샷, parent 체인)
              │     └─ core_parameter_version  ← 입력 숫자의 유일한 집
              │            ├─ core_parameter_evidence ─ core_evidence ─ core_evidence_chunk(pgvector)
              │            └─ core_approval
              ├─ core_scenario (base version + selections + overrides, FIXED 금지)
              │     └─ core_calc_run (engine_version + input_hash 유일) ← 산출 숫자의 유일한 집
              ├─ core_decision (어떤 calc_run을 보고 결정했는가)
              ├─ core_change_request (AI·사람의 숫자 제안)
              ├─ ai_job ─ ai_message(guard_ok, model_used, cost) ─ ai_result(verdict, findings, coach_next)
              ├─ wf_run (Durable 엔진 상태 미러)
              └─ dev_* 도메인 팩: dev_floor, dev_md_option(+_param), dev_party, dev_impact_edge
```

요청된 객체는 이렇게 대응한다.

| 요청 객체 | 대응 테이블 |
|---|---|
| PROJECT / BUILDING / FLOOR / SPACE / UNIT | `core_project`, `dev_floor` (SPACE와 UNIT은 2단계에 `dev_space`, `dev_unit`으로 추가) |
| MD_OPTION | `dev_md_option` |
| SCENARIO | `core_scenario` |
| COST_ITEM / REVENUE_ITEM / PARKING / FINANCING | 파라미터 키 공간 (`cost.*`, `price.*`, `parking.*`, `finance.*`) + calc 노드 |
| CONTRACTOR / EXPERT | `dev_party` |
| DECISION / EVIDENCE / VERSION / APPROVAL | `core_decision`, `core_evidence`, `core_model_version` + `core_parameter_version`, `core_approval` |
| AI_JOB / AI_MESSAGE / AI_RESULT / WORKFLOW_RUN | `ai_job`, `ai_message`, `ai_result`, `wf_run` |

### 6.2 FIXED / ASSUMPTION / OPTION을 데이터 레벨에서 분리하는 법

| 상태 | 정의 | 데이터 규칙 |
|---|---|---|
| **FIXED** | 계약·인허가·실측으로 확정된 값 | APPROVED 승인 + 근거 1개 이상이 **트리거로 강제**된다. 시나리오가 만들 수 없다 |
| **ASSUMPTION** | 기준안에 쓰는 가정 | `confidence`를 사람이 입력한다. EVIDENCE VIEW에서 "낮은 confidence × 높은 민감도" 순으로 정렬해 다음 리서치 대상을 고른다 |
| **OPTION** | 선택지에 딸린 값 (예: KM36의 필요 면적) | MD 옵션 파라미터, 또는 시나리오 override로만 존재한다. 선택될 때만 계산에 들어간다 |
| **DERIVED** | 계산 결과 | **입력 테이블에 저장 불가**(enum에서 제외). CalcRun에만 존재한다 |

**핵심 설계 결정 [INFERENCE]**
- 층(`dev_floor`)에 면적 같은 숫자 컬럼을 두지 않는다. 대신 `area_param_key`로 장부를 가리킨다. 숫자가 두 군데 살면 반드시 어긋난다.
- **Vertical A와의 공유:** `core_*` 테이블(Slot/Option/Scenario/Parameter/Evidence/CalcRun/AI/Approval)은 그대로 쓴다. Vertical A는 `dev_*` 대신 `prd_*` 도메인 팩(상품 슬롯, 채널, SKU 옵션)만 추가한다. 반대로 모든 것을 범용 EAV로 만들면 질의와 무결성이 무너진다. **코어는 범용, 도메인은 타입이 있는 테이블**로 간다.

---

## 7. CALCULATION ENGINE

### 7.1 어디서 계산하나

| 후보 | 판정 | 이유 |
|---|---|---|
| **TypeScript 순수 패키지 (`@dream/calc`)** | **채택** | 브라우저 미리보기와 서버 확정 계산이 **같은 코드**다. 단위테스트와 코드리뷰가 가능하다. 버전 문자열로 식 변경을 추적한다 [FACT: 프로토타입] |
| Python 서비스 | 2단계 옵션 | 몬테카를로·최적화(예: 층별 MD 조합 탐색)가 필요해지면 별도 서비스로 둔다. 같은 테스트 벡터로 TS와 교차검증한다 |
| PostgreSQL Function | 비채택 (검증 제약만) | 테스트·리뷰·배포 흐름이 약하다. 트리거는 "규칙 강제"에만 쓴다 |
| Supabase Edge Function | 호스팅 위치로만 가능 | 계산은 밀리초 단위라 시간 제한 문제는 없다. 다만 Next.js 서버와 코드가 중복된다 |
| Spreadsheet 엔진 | **그림자 모델로만** | 기존 엑셀은 1개월간 **대조용**으로 둔다(같은 입력 → 엑셀과 엔진 결과가 ±0.1% 이내인지 확인). HyperFormula는 GPLv3/상용 이중 라이선스라 제품 내장 전에 법무 확인이 필요하다 **[SOURCE](https://hyperformula.handsontable.com/docs/)** |

### 7.2 AI가 숫자를 임의로 바꾸지 못하게 하는 아키텍처

```
사람/AI ──(change_request: 값 + 근거 + ASSUMPTION/OPTION만)──▶ 승인 ──▶ parameter_version(새 행)
                                                                         │
브라우저 calc (PREVIEW 표시) ◀── 같은 @dream/calc ──▶ 서버 calc ──▶ calc_run(engine_version, input_hash)
                                                                         │
AI ◀────────────── calc_run(읽기 전용) + impact + evidence chunks ────────┘
AI 출력 ──▶ number guard ──▶ [[node_id]]는 calc_run 값으로 렌더링, 날것의 숫자는 불일치 시 거부
```

### 7.3 프로토타입 실행 결과 (DUMMY 입력, 메커니즘 증명용) **[FACT]**

| 시나리오 | 총사업비 | 총수입 | 이익 | BEP 민간분양률 | 주차(공급/필요) | 엔진 플래그 |
|---|---|---|---|---|---|---|
| BASE-132 | 346.6억 | 388.3억 | 41.6억 | 83.6% | 120/114 | – |
| KM36-3F | 364.1억 | 397.5억 | 33.4억 | 86.9% | 120/117 | – |
| KM40-3F | 367.6억 | 401.3억 | 33.8억 | 86.7% | 120/117 | **BLOCK: 3F 면적 107.9㎡ 부족** |
| B3 | 402.9억 | 388.3억 | −14.6억 | 105.8% | 180/114 | WARN: 이익 음수 |

이 표에서 보여주려는 것은 메커니즘이다. **대흥동에 대한 판단이 아니다.** 예를 들어 KM40을 950㎡ 층에 넣으면, AI를 한 번도 부르기 전에 엔진이 면적 부족으로 막는다. 그래서 불가능한 옵션에 AI 비용을 쓰지 않는다.

---

## 8. MAKE vs n8n vs CODE

### 8.1 현재 가설에 대한 비판

> 가설: Make = SEND/ROUTE/CONNECT, n8n = WAIT/RESUME/STATE/LONG WORKFLOW

- **사실 관계는 맞다.**
  - n8n Wait 노드는 resume URL·폼·시간으로 재개된다 **[SOURCE](https://osher.com.au/tools/wait/)**.
  - Make 시나리오는 실행 시간 상한이 40분(+5분 유예)이다. 긴 대기는 시나리오를 쪼개 웹훅으로 이어야 한다 **[SOURCE](https://community.make.com/t/maximum-execution-timeout-40-minutes-error-handler-notification/23773.md)**.
- **그러나 결론은 틀렸다고 본다 [INFERENCE].**
  - 350억 사업에서 가장 중요한 로직은 "**기다리고, 상태를 갖고, 승인 후 재개하는 것**"이다. 이것을 비주얼 도구에 두면 코드리뷰, 단위테스트, 배포 버전관리, 재실행 의미론이 약해진다.
  - 도구 두 개는 인증정보·모니터링·장애 지점·학습비용을 **두 배**로 만든다.
  - 상태는 **코드로 된 Durable Workflow**가 갖는다. Make/n8n은 **상태 없는 가장자리 커넥터**(Slack·메일·Drive·Notion·캘린더)로 쓴다.

### 8.2 다섯 가지 아키텍처 비교 (5점 = 좋음) **[INFERENCE]**

| 기준 | A. Make 중심 | B. n8n 중심 | C. Make+n8n | D. Code-first | **E. Durable 엔진 + 가장자리 1개** |
|---|---|---|---|---|---|
| Reliability | 3 | 3 | 2 | 4 | **5** |
| State | 1 | 3 | 2 | 3 | **5** |
| Long-running Job | 1 (40분) | 4 | 3 | 2 (직접 구현) | **5** |
| Human Approval | 2 | 4 | 3 | 3 | **5** (waitForEvent) |
| AI Agent | 3 | 4 | 3 | 5 | **5** |
| Failure Recovery | 2 | 3 | 2 | 3 | **5** (단계별 재시도·재생) |
| Observability | 3 | 3 | 2 | 3 | **4** |
| Versioning | 2 | 2 (JSON export) | 1 | 5 | **5** |
| Cost | 3 | 4 (셀프호스트) | 2 | 4 | **4** |
| Complexity (낮을수록 5) | 4 | 3 | 1 | 3 | **3** |

### 8.3 추천

**E안이다.** 구체적으로는 이렇다.
- **Durable 엔진:** Next.js + Vercel을 쓰면 **Vercel Workflow** 또는 **Inngest** 중 하나를 고른다.
  - Vercel Workflow: 2025년 10월 오픈소스 WDK 공개 베타, 이후 GA **[SOURCE](https://vercel.com/changelog/open-source-workflow-dev-kit-is-now-in-public-beta)**.
  - Inngest: 무료 구간이 있고 운영 부담이 없다 **[SOURCE](https://automationatlas.io/guides/inngest-vs-temporal-2026-comparison/)**.
  - Temporal은 이 규모에서는 과하다 [INFERENCE].
- **가장자리:** Make 또는 n8n 중 **팀이 이미 익숙한 하나**를 쓴다. 앞서 리서치팀 기획을 Make로 시작했으니 **Make 유지, n8n은 도입하지 않는다**. 다만 데이터 국외 반출 제한이나 자체 호스팅 요구가 생기면 n8n으로 **교체**한다(병행하지 않는다).
- 워크플로 계약서: `prototype/contracts/workflow.md`.

---

## 9. FLOW / DEPENDENCY ENGINE

### 9.1 Workflow ≠ Dependency Graph

| | Workflow | Calc Dependency Graph (DAG) | Impact Graph |
|---|---|---|---|
| 질문 | "다음에 **누가 무엇을** 하나?" | "이 숫자가 바뀌면 **어떤 숫자가** 바뀌나?" | "이 결정이 바뀌면 **어떤 검토·인허가·일정**이 흔들리나?" |
| 성격 | 시간 순서, 사람·AI 작업 | 산술, 결정론 | 정성적, 전문가 지식 |
| 출처 | 워크플로 코드 | **계산 코드에서 자동 추출**(deps 선언) | 사람이 큐레이션 (`dev_impact_edge`) |
| 예 | 리뷰 → 반박 → 사실확인 → 승인 | 3F 옵션 → 면적여유·주차·TI → 직접비 → PF → 금융비 → 총사업비 → 이익·BEP | B3 → 지하수·흙막이 → 굴착 인허가 → 공기 → 금융기간 |

### 9.2 구현

- **Calc DAG:** 위상정렬(Kahn), downstream(영향 노드), upstream(lineage). 순환은 거부한다. 프로토타입 `graph.ts`에 있다 **[FACT]**.
- 실제 출력 예 — 3F BASE → KM36의 영향 경로 (자동 탐지) **[FACT]**:
  `floor.3F.area_headroom_m2 → parking.podium_required → parking.required → parking.shortfall → podium.annual_rent → podium.fitout_capex → cost.direct → cost.soft → finance.pf_amount → cost.finance → cost.total → podium.value → bep.private_sale_rate → rev.total → profit → profit.rate_on_cost`
  - LH 수입(`rev.lh`)은 영향 목록에 **들어가지 않는다**. 테스트로 확인했다.
- **Impact Graph:** 계산이 아닌 관계(인허가·검토·일정)를 표로 두고, 옵션 선택 시 `review_roles`를 소집한다.
- **Rule engine은 별도로 두지 않는다.** 규칙은 (a) 엔진 플래그(BLOCK/WARN), (b) DB 제약, (c) 워크플로 분기 세 곳에만 둔다 [INFERENCE]. 규칙 엔진을 따로 두면 숫자 규칙이 네 번째 장소에 생긴다.
- **Reactive 계산:** 입력 변경 → downstream만 재계산하는 것은 스프레드시트와 같은 원리다. 노드 수백 개면 전체 재계산도 밀리초 단위라, MVP는 전체 재계산 후 diff로 충분하다 [INFERENCE: 데모가 즉시 실행됨].

### 9.3 화면

- React Flow + ELK 계층 레이아웃. 노드 색은 입력의 상태(FIXED 녹색 / ASSUMPTION 주황 / OPTION 파랑), 테두리는 플래그다.
- 옵션 선택 시 **영향 경로만 강조**하고, 엣지 라벨에 Δ값을 표시한다.
- 노드를 클릭하면 upstream lineage와 근거 목록이 나온다 (EVIDENCE VIEW와 같은 데이터).

---

## 10. MULTI-AI ARCHITECTURE

```
UI (Role만 앎) ─▶ AI Job API ─▶ Role Registry ─▶ Router ─▶ AI Gateway ─▶ {Claude, GPT, Gemini, Grok, …}
                                   │ prompt, tools, output schema, model policy
                                   ▼
                       Context Packer (building_state 투영 + calc_run + impact + evidence chunks)
                                   ▼
                       Structured Output 검증 → Number Guard → ai_message/ai_result 저장 → Realtime
```

| 요소 | 추천 | 근거 |
|---|---|---|
| Role Registry | DB 또는 코드의 역할 정의: 프롬프트, 허용 도구, 출력 스키마, 모델 정책(1순위·대체·금지) | 프로토타입 계약서 `ai-job.schema.json` |
| AI Gateway | Vercel에 있으면 **Vercel AI Gateway**, 자체 호스팅이 필요하면 **LiteLLM**, 관측·가드레일 중심이면 **Portkey** | Vercel AI Gateway는 Vercel 밖에서 못 쓰고 ZDR 정책이 있다. Portkey는 OSS + 관리형 **[SOURCE](https://mcp.directory/blog/vercel-ai-gateway-vs-portkey-vs-openrouter-vs-litellm-2026)** |
| MCP | **읽기 도구만** MCP 서버로 연다: `get_building_state`, `get_calc_lineage`, `search_evidence`. 쓰기는 `propose_change` 하나뿐 | AI 쓰기 권한 최소화 [INFERENCE] |
| Structured Output | 모든 역할이 같은 `ai-result@0` 스키마로 출력 | 공급자를 바꿔도 화면·DB가 바뀌지 않는다 |
| Context / Evidence Passing | 전체 DB가 아니라 **impacted inputs만 투영**한다. 근거는 chunk_id로 전달하고, 주장은 evidence_id로 인용 | 토큰 절감, 인용 검증 가능 |
| Cost Routing | 분류·요약은 소형 모델, 검토는 중형, 반박·종합은 대형. 역할별 월 예산 상한 | |
| Fallback | 같은 등급의 다른 공급자로 대체하고, `model_used`를 기록 | 감사 추적 |
| Observability | 게이트웨이 로그 + 트레이스 도구(예: Langfuse 같은 오픈소스) + `ai_message.cost_usd` 집계 | [INFERENCE] |
| **보안** | PF 조건, 임차 협상 조건 같은 민감 데이터는 **데이터 보존 없음(ZDR)** 공급자로만 라우팅한다 | [INFERENCE] |

**비판:** 처음부터 공급자 4개를 쓸 필요는 없다. **MVP는 공급자 1~2개**로 시작한다. 다른 계열 모델은 **Challenger에만** 쓴다(§11). 라우터는 처음엔 "역할 → 고정 모델" 표로 충분하다. 자동 라우팅은 품질 데이터가 쌓인 뒤에 도입한다. [INFERENCE]

---

## 11. AI TALK / REVIEW / COACH

### 11.1 연구가 말하는 것

- 다중 에이전트 토론(MAD)은 **항상 나은 게 아니다**. 자기일관성(self-consistency)이나 앙상블보다 안정적으로 낫지 않다. 매번 토론을 돌리면 비용이 크고, 맞던 답을 뒤집기도 한다 **[SOURCE](https://proceedings.mlr.press/v235/smit24a.html)**, **[SOURCE](https://arxiv.org/abs/2509.05396v2)**.
- **필요할 때만 토론**시키는 적응형 방식이 효율적이다 **[SOURCE](https://arxiv.org/html/2504.05047v2)**.
- 같은 모델끼리의 토론은 아첨(sycophancy)과 합의 붕괴 위험이 있다 **[SOURCE](https://caisconf.org/program/2026/papers/decomposing-sycophancy-fragility-consensus-collapse-and-cost-in-homogeneous-mult/)**.

### 11.2 품질이 오르는 조건 vs 비용만 느는 조건 **[INFERENCE]**

| 품질이 오른다 | 비용만 는다 |
|---|---|
| 역할마다 **다른 근거·도구**를 가진다 (의료법 문서 vs 주차 조례 vs 금융 조건) | 모든 에이전트가 같은 문맥을 받고 같은 질문에 답한다 |
| Challenger가 **다른 계열 모델**이다 | 같은 모델이 페르소나만 바꿔 토론한다 |
| 결과가 **검증 가능**하다 (근거 인용, 엔진 숫자) | 결과가 의견뿐이라 검증할 수 없다 |
| 영향이 큰 결정에만 소집한다 | 매 클릭마다 전원 소집한다 |
| 라운드 상한(2)과 종료 조건이 있다 | 합의할 때까지 토론한다 |

### 11.3 운영 규칙 (프로토타입 workflow에 반영)

1. **엔진이 먼저 판단한다.** BLOCK이면 AI를 부르지 않는다.
2. **소집:** 영향 그래프가 지목한 역할만 부른다. 실데이터의 3F → KM36이라면 의료·법률·MEP/소방·주차·재무 리뷰어가 해당한다.
3. **Challenger 발동 조건** (하나라도 해당하면):
   - 리뷰어 중 SUPPORT가 아닌 판정이 있다.
   - 이익 변화가 임계값을 넘는다.
   - 입력 중 confidence가 0.5 미만인 것이 영향 경로에 있다.
4. **라운드는 최대 2회.** 그 뒤 FACT_CHECKER가 SOURCE/FACT 주장을 근거 chunk와 대조한다.
5. **AI COACH의 출력은 다음 행동 하나뿐**이다: `CONTINUE / DEEPEN / CHALLENGE / VERIFY / REFRAME / STOP`. 코치는 결론을 내리지 않는다. 다음 리서치는 "**민감도는 높고 confidence는 낮은 파라미터**" 순으로 제안한다. 이 순서는 계산으로 정해지고, AI는 그 이유를 설명만 한다.
6. **측정:** 역할별로 다음 세 가지를 기록해, 분기마다 쓸모없는 역할을 정리한다.
   - 사람이 받아들인 지적의 비율
   - 그 지적 하나를 얻는 데 든 비용
   - 근거 대조를 통과한 주장의 비율

---

## 12. DIGITAL TWIN / BIM STRATEGY

### 12.1 이름

- Digital Twin Consortium의 정의는 "실세계 개체·프로세스의 가상 표현으로서 **지정된 주기와 충실도로 동기화**되는 것"이다 **[SOURCE](https://www.digitaltwinconsortium.org/2020/12/digital-twin-consortium-defines-digital-twin)**.
- 지금 대흥동에는 동기화할 실물(센서, 준공 건물)이 없다. 그래서 "Digital Twin"이라고 부르면 투자자·전문가에게 과장으로 읽힐 위험이 있다 [INFERENCE].
- 그런데 동기화 대상을 **실물이 아니라 사업 상태**(결정·견적·인허가·근거)로 보면 정의를 충족한다. 갱신 주기는 "결정 시점"이다 [INFERENCE].

| 후보 | 평가 |
|---|---|
| Digital Twin | ✗ 과장, 오해 소지 |
| Business Digital Twin | △ 뜻은 맞지만 너무 넓다 |
| **Development Decision Twin** | ✓ **외부 공식 명칭으로 추천.** 정확하다 |
| **Computable Building** | ✓ **제품·UX 이름으로 추천.** 직관적이다 |

### 12.2 BIM은 언제 연결하나

| 단계 | 데이터 | BIM |
|---|---|---|
| 지금 ~ 계획설계 | Floor / Space 장부 (층별 면적·용도) | **불필요.** 숫자 결정의 대부분이 이 단위에서 일어난다 [INFERENCE] |
| 기본설계 | 건축사 모델에서 **IFC 내보내기 → 공간별 면적 추출**(IfcOpenShell 등) → 장부와 **대조** | **연결 1단계.** BIM은 근거(Evidence)의 한 종류로 들어온다 |
| 실시설계 ~ 시공 | 물량·공정 연동 (Togal류 적산, 공정 도구) | 연결 2단계. 필요하면 Speckle 같은 데이터 통로 |
| 준공 후 | 센서·운영 | 이때 비로소 진짜 Digital Twin |

- **규제 메모:** 국토부 BIM 의무화는 공공공사 중심으로 단계 확대 중이다(보도상 1000억 → 500억 이상) **[SOURCE](https://www.cbilder.com/2026/08/2026-bim.html)**. 민간 350억 사업은 대상이 아닐 가능성이 높다 **[INFERENCE]**.
- **확인 필요:** LH 매입약정 물량(55호)에 LH가 별도 BIM·도서 요건을 붙이는지 **[ASSUMPTION — LH 확인 필요]**.

---

## 13. PROTOTYPE CODE / SCHEMA

전부 `prototype/`에 있다. 설치 없이 Node 22만으로 실행된다.

| 요청 항목 | 파일 | 상태 |
|---|---|---|
| Repository Structure | `prototype/README.md` | ✓ |
| Database Schema | `db/schema.sql` | ✓ PostgreSQL 16 적용, FIXED 트리거·CHECK 제약 동작 확인 [FACT] |
| TypeScript Interfaces | `packages/core/types.ts` | ✓ |
| API Contract | `contracts/api.md` | ✓ |
| Scenario JSON | `scenarios/*.json` | ✓ DUMMY |
| Calculation Function | `packages/calc/model.ts`, `engine.ts` | ✓ 테스트 10/10 통과 [FACT] |
| AI Job Contract | `contracts/ai-job.schema.json` | ✓ |
| Workflow Contract | `contracts/workflow.md` | ✓ (엔진 중립 의사코드) |
| WebSocket / Realtime Pattern | `apps/web/STRUCTURE.md` | ✓ |
| Frontend Component Structure | `apps/web/STRUCTURE.md` | ✓ |
| Dependency Graph Data Structure | `packages/calc/graph.ts` (+ `edges()`는 React Flow 입력) | ✓ |

### Building → Floor → Option → Scenario → Calculation → AI Review 연결 (코드상)

```ts
const model    = loadModel();                                   // Building + Floors + Option catalog + Parameter ledger
const base     = loadScenario("base-132");                      // selections {1F,2F,3F: COMMERCIAL}
const next     = { ...base, id: "KM36-3F", selections: { ...base.selections, "3F": "KM36" } }; // CLICK 1 + CLICK 2
const run      = engine.run(model, next);                       // resolve → validate → evaluate → inputHash
const impact   = engine.impact(model, base, next);              // changedInputs → impactedNodes → deltas → reviewRoles
if (!run.flags.some(f => f.severity === "BLOCK"))
  workflow.send("scenario-review", { from: base.id, to: next.id }); // roles from impact, challenger by rule, human gate
const shown    = renderAiText(aiSummary, run);                  // [[profit]] → 엔진 값. guardAiText()가 날조 숫자 거부
```

---

## 14. THREE ARCHITECTURE OPTIONS

| 기준 | OPTION 1 — RAPID (Lovable + Supabase + Make/n8n + AI API) | **OPTION 2 — PRODUCTION (Next.js + Vercel + Supabase + Calc Engine + 가장자리 1개 + AI Router)** | OPTION 3 — ADVANCED (Custom + State layer + Durable + Dependency engine + Multi-AI control plane + BIM) |
|---|---|---|---|
| BUILD TIME | 1~2주 | **4~6주** (MVP 30일) | 4~6개월 |
| COST | 낮음 | **중간** | 높음 (전담 2~4명) |
| TECHNICAL DEBT | **높음** — 계산이 UI 코드에 섞이고, 브랜치·리뷰가 약하다 | 낮음~중간 | 낮음. 단 과잉설계 부채가 생긴다 |
| SCALABILITY | 낮음 | 높음 | 매우 높음 |
| AI CONNECTIVITY | 중간 (프론트에서 직접 호출하기 쉽다 → 위험) | **높음** (서버 게이트웨이) | 매우 높음 |
| REALTIME | 중간 | 높음 | 매우 높음 |
| MAINTAINABILITY | 낮음 | **높음** | 중간 (복잡도 때문) |
| DREAM DATA FACTORY REUSE | 낮음 | **높음** (core_* + 도메인 팩) | 높음 |

**판정 [INFERENCE]**
- **OPTION 2를 기본으로 한다.**
- OPTION 1은 1주차 UX 시안에만 쓴다.
- OPTION 3의 요소는 **조건이 생겼을 때만** 들인다. 예: 대흥동 다음 사업이 2개 이상 → 포트폴리오 그래프. 기본설계 도달 → IFC 대조.

---

## 15. RISKS / COUNTERARGUMENTS

### 15.1 DREAM의 현재 생각에 대한 반론

| 질문 | 내 답 |
|---|---|
| 너무 복잡한 부분은? | **AI TALK의 자유 토론, 3D 건물, 자동 모델 라우팅, Make+n8n 병행, 실시간 다중 사용자 편집.** 첫 사업의 의사결정 품질에 기여하는 정도가 작다 [INFERENCE] |
| Make+n8n 둘 다 필요한가? | **아니다.** 상태는 코드(Durable)에 두고, 가장자리는 하나만 쓴다 (§8) |
| Lovable은 어디까지? | **화면 시안까지만.** 계산·권한·워크플로가 들어가는 순간 OPTION 2로 옮긴다 |
| BIM을 너무 일찍 도입하나? | **그렇다**, 지금 도입한다면. 기본설계 IFC 대조부터 시작한다 (§12) |
| Multi-AI가 과한가? | 전원 토론은 과하다. **역할 분리(근거·도구가 다름) + 선택적 Challenger**는 가치가 있다 (§11) |
| AI가 해서는 안 되는 계산은? | **모든 산술**: 공사비, 금융비, 수입, 이익, BEP, 용적률·건폐율 산정, 법정주차 대수, 세대수 합계, 민감도. AI가 해도 되는 것은 **입력 후보 조사·근거 요약·결과 설명·반박 질문**이다 |
| 사람이 승인해야 하는 데이터는? | 아래 §15.2 Human Gate |

### 15.2 Human Gate (반드시 사람)

1. 파라미터를 **FIXED로 승격**할 때 (트리거로 강제)
2. **근거를 채택**할 때 (`core_evidence.verified_by`)
3. 시나리오를 **BASE로 승격**할 때
4. **ENGINE_VERSION 변경** 배포 (식이 바뀌면 과거 결과와 비교 리포트 첨부)
5. AI의 `change_request`를 반영할 때
6. **외부 발송**: LH, 대주(PF), 임차인, 시공사에 나가는 모든 숫자
7. 법률·인허가 상태의 변경 (AI는 "확인 필요"까지만)

### 15.3 350억 사업에서 시스템 오류의 위험

| 위험 | 시나리오 | 대응 |
|---|---|---|
| **계산식 버그의 증폭** | 식 하나의 1% 오류 ≈ 3.5억 [INFERENCE: 단순 비례] | 엑셀 그림자 모델 대조 1개월, 테스트 벡터, 엔진 버전 승인 |
| **거짓 정밀도** | ASSUMPTION 숫자가 소수점까지 표시돼 확정처럼 보인다 | 상태 색상 표시, confidence 낮은 값의 유효숫자 제한, "가정 비중" KPI |
| **AI의 법규 환각** | 의료시설 기준·주차 조례를 그럴듯하게 틀린다 | 법률 역할은 근거 chunk 없이 FACT를 낼 수 없다. FACT_CHECKER, 전문가 승인 |
| **낡은 근거** | 6개월 전 견적이 계속 쓰인다 | 근거에 `issued_on`, 만료 경고 |
| **버전 혼동** | 회의에서 서로 다른 숫자를 본다 | 모든 화면·PDF에 `scenario + input_hash 앞 8자리` 표기 |
| **기밀 유출** | PF 조건·임차 협상 조건이 AI 공급자에 남는다 | ZDR 라우팅, 민감 필드 마스킹, 역할별 문맥 최소화 |
| **벤더 종속** | 생성형 빌더·특정 AI에 묶인다 | 계산·계약·스키마는 모두 저장소의 코드 |
| **과잉 설계** | 시스템 만드느라 사업 결정이 늦어진다 | 30일 MVP, 기능 버리기 목록(§16.3) |

---

## 16. RECOMMENDED MVP — DAEHEUNG COMPUTABLE BUILDING

### 16.1 목표 UX

```
CLICK 1  3F 선택 ─▶ FloorPanel: 면적·현재 용도·상태·관련 숫자·근거 (네트워크 없음)
CLICK 2  KM36 선택
   ├─ [0.01초] 브라우저 calc → PREVIEW Δ (총사업비, 이익, BEP, 주차)
   ├─ [~1초] 서버 calc → calc_run 저장, input_hash 일치 확인 → PREVIEW 꼬리표 제거
   ├─ impact → FLOW VIEW에 영향 경로 강조
   ├─ BLOCK? → 멈춤 + 사유 표시 (AI 호출 없음)
   ├─ scenario-review 워크플로 시작 → 지목된 역할만 검토 → (조건부) Challenger → Fact Check
   ├─ AI COACH: 다음 행동 1개 + 이유
   └─ ApprovalCard: 사람이 승인/반려  ◀── HUMAN GATE
```

### 16.2 MVP 범위 (넣는다)

- 층 15개 + 지하 2~3개를 **Floor 단위**로 다룬다. Space와 Unit은 2단계.
- 옵션 6종: COMMERCIAL / ANCHOR_BAKERY / ANCHOR_RETAIL / KM30 / KM36 / KM40
- 시나리오 4개 이상: BASE-132 / KM36-3F / KM40-3F / B3
- 7개 뷰를 단순하게 구현한다. 3D 없음, SVG 스택.
- 파라미터 장부 + 근거 업로드 + 승인
- 역할 5개: 의료, 법률, 재무, 공사, Fact Checker. Challenger는 다른 계열 모델 1개. Coach.
- 엑셀 그림자 대조 리포트

### 16.3 MVP에서 반드시 버릴 것

1. 3D / BIM / IFC
2. AI끼리의 자유 대화 (라운드 상한 없는 토론)
3. 자동 모델 라우팅 (역할 → 고정 모델 표로 충분)
4. Make와 n8n 병행
5. 생성설계 / 자동 층 배치 최적화
6. 공정(스케줄) 자동화
7. 다중 사용자 동시 편집
8. 일반화된 "아무 사업이나" 지원 — 대흥동 하나에 맞춘다. 코어 테이블만 범용으로 둔다.

---

## 17. 30-DAY BUILD ROADMAP

| 주 | 목표 | 산출물 | 완료 기준 |
|---|---|---|---|
| **1주차** | 데이터와 숫자 규율 | Supabase 스키마, 기존 엑셀·PDF → 파라미터 장부 이관(상태·근거 표시), Lovable로 층 스택 UX 시안 → 합의 후 폐기 | 모든 입력 숫자에 상태가 붙음. FIXED는 근거·승인 포함 |
| **2주차** | 계산 엔진 + Building View | `@dream/calc` 대흥동 식 확장(용적률·건폐율·법정주차 규칙 팩), 엑셀 그림자 대조, Next.js 층 스택 + Floor Panel + KPI | BASE-132가 엑셀과 ±0.1% 이내. CLICK 1→2 미리보기 동작 |
| **3주차** | 시나리오·근거·영향 | Scenario View, Evidence View(lineage), Flow View(React Flow), CalcRun 저장·해시 표기 | KM36/KM40/B3 비교, 영향 경로 시각화, 모든 숫자에서 근거까지 2클릭 |
| **4주차** | AI 검토 + Human Gate | Durable 엔진 1개 도입, scenario-review 워크플로, AI Gateway + 역할 5개 + Challenger + Coach, number guard, ApprovalCard, Make 가장자리 알림 | 3F→KM36 실데이터로 검토 → 승인까지 완주. 날조 숫자 0건. 역할별 비용 대시보드 |

**30일 이후:** Space/Unit 모델, 민감도·몬테카를로, IFC 대조(기본설계 시점), Vertical A 도메인 팩.

---

## 18. FINAL RECOMMENDATION

**FINAL QUESTION에 대한 답:**

> 2026년 현재 가장 현실적인 구조는 다음과 같다.
> - **Frontend:** Next.js(React) + Vercel. 커스텀 SVG Building Stack과 React Flow를 쓴다. Lovable은 시안용.
> - **Backend:** Supabase Postgres 하나를 진실의 원천으로 둔다. 입력은 Parameter 장부, 산출은 CalcRun, 근거는 Storage + pgvector에 둔다.
> - **Calculation:** 브라우저와 서버가 공유하는 결정론적 TypeScript 엔진. 엔진 버전 + 입력 해시로 증명하고, 엑셀 그림자 모델로 1개월 검증한다.
> - **Workflow:** 코드 기반 Durable Workflow 엔진 하나가 상태·대기·승인을 맡는다. Make 하나는 상태 없는 가장자리 커넥터로만 쓴다.
> - **Multi-AI:** 역할 레지스트리 + AI Gateway. 쓰기는 `propose_change` 하나뿐이고, 숫자는 자리표시자로만 말한다. 다른 계열 모델은 선택적 Challenger에만 쓴다.

이 구조의 가치는 기술 선택이 아니라 **데이터 규율**에서 나온다 [INFERENCE].
- FIXED / ASSUMPTION / OPTION 장부
- 결정론적 엔진
- 영향 그래프
- 사람 승인

이 네 가지가 대흥동에서 작동하면, 같은 `core_*` 위에 도메인 팩만 바꿔 Vertical A(상품·콘텐츠·커머스)로 확장할 수 있다. 그것이 DREAM DATA FACTORY의 공통 OS다. 반대로 이 네 가지 없이 화면과 AI부터 만들면, 숫자가 그럴듯하게 틀리는 비싼 챗봇이 된다.

**다음 행동 (DREAM에게)**
1. 대흥동 현재 엑셀과 PDF 목록을 주면, 1주차 파라미터 장부 이관표(키·값·상태·근거·confidence)를 만든다.
2. KM30/36/40 ↔ 240/260/320평 대응, 의료시설 기준, 주차 원단위를 **ASSUMPTION → 근거 확보 대상** 목록으로 지정한다.
3. Durable 엔진(Vercel Workflow 또는 Inngest)과 가장자리 도구(Make 유지 여부)를 결정한다.

---

## Sources

- TestFit 비교·대안: https://www.nomic.ai/compare/testfit-alternatives
- TestFit 외부 AI 연결(2026-09): https://www.testfit.io/news/at-dallas-testfit-ai-assistants-can-now-guide-real-estate-feasibility-studies
- 호주 개발 도구(Archistar 등): https://www.feasly.com.au/guides/property-development-apps-digital-tools-australia
- Giraffe: https://landchecker.com.au/articles/landchecker-partner-with-3d-design-platform-giraffe/
- Deepblocks: https://urbanland.uli.org/economy-markets-trends/ul-interview-a-deep-dive-on-deepblocks-bringing-demographic-data-to-pro-forma-modeling
- Autodesk 에이전트형 AI(AU 2026): https://macaubusiness.com/autodesk-advances-agentic-ai-in-its-three-industry-clouds/
- Procore Groundbreak 2025: https://www.businesswire.com/news/home/20251015796723/en/Procore-Advances-the-Future-of-Construction-with-New-AI-Innovations-at-Groundbreak-2025
- ALICE 2025 연간 리뷰: https://blog.alicetechnologies.com/alices-2025-annual-review
- Togal.AI: https://www.capterra.com/p/10001876/Togal-AI/
- Speckle: https://aecmag.com/features/speckle-the-open-source-cloud-data-platform/
- Sketch2BIM(관련 연구 개관 포함): https://arxiv.org/pdf/2510.20838
- LLM 다중 에이전트 DT 파라미터화: https://arxiv.org/pdf/2405.18092
- Awesome-AECO: https://github.com/osama-ata/Awesome-AECO
- Digital Twin Consortium 정의: https://www.digitaltwinconsortium.org/2020/12/digital-twin-consortium-defines-digital-twin
- 국토부 BIM 확대(2026): https://www.cbilder.com/2026/08/2026-bim.html
- Lovable 한계: https://rapidevelopers.com/lovable-issues/lovable-limitations-and-production-readiness
- React Flow / xyflow: https://landscape.jimmysong.io/projects/xyflow/
- HyperFormula 라이선스: https://hyperformula.handsontable.com/docs/
- Supabase Realtime 한계: https://supabase.com/docs/guides/realtime/limits.md
- Make 40분 제한: https://community.make.com/t/maximum-execution-timeout-40-minutes-error-handler-notification/23773.md
- n8n Wait 노드: https://osher.com.au/tools/wait/
- Vercel Workflow DevKit: https://vercel.com/changelog/open-source-workflow-dev-kit-is-now-in-public-beta
- Inngest vs Temporal 2026: https://automationatlas.io/guides/inngest-vs-temporal-2026-comparison/
- AI Gateway 비교 2026: https://mcp.directory/blog/vercel-ai-gateway-vs-portkey-vs-openrouter-vs-litellm-2026
- MAD 비판(ICML 2024): https://proceedings.mlr.press/v235/smit24a.html
- 적응형 토론: https://arxiv.org/html/2504.05047v2
- 선택적 토론(iMAD): https://arxiv.org/abs/2509.05396v2
- 동질 다중 에이전트의 아첨·합의 붕괴(CAIS 2026): https://caisconf.org/program/2026/papers/decomposing-sycophancy-fragility-consensus-collapse-and-cost-in-homogeneous-mult/
