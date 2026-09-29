---
id: CLAUDE-PRD-001
lab: CLAUDE-PRINCIPAL-RD-01
title: DREAM AGENTIC INTELLIGENCE — MINIMUM KERNEL RESEARCH
status: proposed
authority: research / design only
approved: false
sensitivity: none
source_ai: claude
date: 2026-09-29
---

# CLAUDE-PRD-001 — DAIS Minimum Kernel: Principal Research Architecture

> 상태: **proposed**. HQ 검토 전 연구 문서다. `approved` 페이퍼가 아니므로
> `index.json` / `insights.json` 에 올리지 않는다. 코드 없음. Prototype 없음.
> DAIS 는 연구명이며 DREAM OS LOCK / DREAM COM 공식 명칭을 바꾸지 않는다.

---

## 0. 먼저 밝혀 둘 사실 (Evidence of what was actually inspected)

이 LOT 에서 실제로 읽은 것은 `biztradepros/grok-knowledge-01` 저장소 전체(13개 파일)뿐이다.

| 브리프가 말한 자산 | 이 저장소에서 확인 | 판정 |
|---|---|---|
| DREAM COM, PROJECT-002, HQ, Knowledge Refinery, Evidence Pack, Remote Adapter, Digital Twin, KTX DOCK 등 | **코드·스펙 없음** | UNVERIFIED — 역할 설명만으로 판단 |
| GitHub 이슈 대기열(`inbox`) + 사람만 붙이는 `approved` 라벨 + `vet-inbox.yml` 형식 검사 + raw markdown 공개 원본 | **실재, 동작 중** | 실재하는 유일한 선행 사례 |

따라서 §4 의 KEEP/ADAPT 판정은 **"설명된 역할이 사실이라면"** 이라는 조건부다.
반대로, 이 저장소의 `inbox → vet → human approved → canon` 흐름은 이미
**mailbox + deterministic admission + human gate + promotion** 의 최소 실물이다.
이 사실이 아래 커널 설계의 가장 강한 근거다.

선행 연구 인용(§2)은 배경 지식에 근거하며 이 LOT 에서 원문을 재검증하지 않았다.

---

## PROBLEM DEFINITION

### 질문
> 중앙 super-agent 없이, 여러 독립 AI persona 가 하나의 long-horizon
> research/engineering task 를 이어서 수행하게 하는 **가장 작은 kernel** 은 무엇인가?

### 문제를 정확히 자르기
"중앙이 없다"는 말은 두 가지를 섞는다. 분리해야 한다.

| | 중앙 **추론자** (central reasoner) | 중앙 **상태 권위** (central state authority) |
|---|---|---|
| 정체 | LLM 이 계획·배정·요약·판단을 모두 한다 | 결정적(deterministic) 규칙이 상태 변경을 받거나 거절한다 |
| 필요성 | **없애야 할 것** | **없앨 수 없는 것** — 없으면 "지금 task 가 어디까지 왔나"에 답이 없다 |
| 실패 시 | 맥락·판단·자격증명 전부 소실 | 로그를 replay 하면 복구 |

**가설 H0**: long-horizon 신뢰성에 필요한 "중심"은 지능이 아니라
**append-only 기록 + 결정적 승인 규칙** 이다. 지능은 전부 가장자리(persona)에 둔다.

### Long-horizon 이 실제로 깨지는 지점
1. **상태가 대화 맥락 안에 산다** → 맥락 소실 = task 소실.
2. **요약이 원본을 대체한다** → 몇 번의 handoff 후 요약의 요약이 사실을 지운다.
3. **누가 무엇을 했는지 서술로만 남는다** → 감사 불가.
4. **동시성/중복** → 같은 step 을 두 AI 가 하거나, 늦게 온 결과가 새 결과를 덮는다.
5. **합의가 증거로 둔갑** → AI 셋이 동의하면 맞는 것으로 처리된다.

커널은 이 다섯 개만 막으면 된다. 그 이상은 커널이 아니다.

---

## 1. ARCHITECTURE COMPARISON (A–F)

점수는 매기지 않는다. 구체적 trade-off 만 적는다.

### A. Central Orchestrator Agent (AutoGen GroupChat manager, CrewAI hierarchical, Magentic-One orchestrator 류)
- **상태 소유**: orchestrator 의 context window. Magentic-One 이 "task ledger / progress ledger" 를 두지만 그 ledger 는 orchestrator 프롬프트 안의 텍스트다 — 즉 LLM 이 쓰고 LLM 이 읽는 서술.
- **깨지는 조건**: 맥락이 창 크기를 넘거나, orchestrator 세션이 끊기거나, orchestrator 가 잘못 요약할 때. 단일 실패점이면서 단일 판단점.
- **자격증명**: 모든 도구를 배정하므로 모든 권한을 가져야 한다. prompt injection 하나의 폭발 반경이 시스템 전체.
- **감사/replay**: LLM 호출은 비결정적이라 replay 가 "재실행"이지 "재현"이 아니다.
- **장점(실재함)**: 만들기 가장 쉽고, 짧은 task 에선 가장 빠르다. 비교 기준선(baseline)으로 쓸 가치가 있다.

### B. ROOM-13 / Switchboard
- 라우터가 메시지를 올바른 수신자에게 연결한다.
- **장점**: 수신자 검증·주소 체계·권한 없는 전달(COMMUNICATION ≠ AUTHORITY)을 자연스럽게 표현.
- **깨지는 조건**: switchboard 는 "누구에게 보낼지"는 알지만 "task 가 어디까지 왔는지"는 모른다. 상태를 붙이는 순간 A 로 퇴화하거나, 메시지 로그가 사실상의 상태가 된다(메시지 ≠ 상태).
- **커널 판정**: 전송(transport) 층으로 적합. 상태 권위로는 부적합.

### C. Blackboard / Mailbox (Hearsay-II 이후 blackboard 계열, Linda tuple space, MetaGPT 공유 message pool)
- **상태 소유**: 공유 게시판. persona 는 읽고 쓴다.
- **장점**: 중앙 추론자 없음. persona 교체 자유. 이 저장소의 이슈 대기열이 바로 이것.
- **깨지는 조건**: 게시판이 **변경 가능(mutable)** 하면 누가 언제 무엇을 덮었는지 사라진다(GitHub 이슈 댓글도 편집·삭제 가능). 동시 쓰기 규칙이 없으면 중복/유실. "누가 다음에 할지"를 정하는 제어 문제가 남는다(고전 blackboard 는 이걸 control shell 로 풀었고, 그게 사실상 중앙 스케줄러가 됐다).
- **커널 판정**: 핵심 뼈대. 단 append-only + 승인 규칙 + claim/lease 가 추가돼야 한다.

### D. Actor-style independent agents (Hewitt actor, Erlang/OTP)
- **상태 소유**: 각 actor 가 자기 상태를 소유, 메시지로만 소통.
- **장점**: failure/context/credential 격리가 가장 강하다. "let it crash" + supervisor 재시작.
- **깨지는 조건**: task 전체 상태가 여러 actor 에 흩어진다. 누가 전체 진행을 아는가? 결국 "task actor" 하나가 필요해지고, 그게 LLM 이면 A 가 된다. 또한 LLM persona 는 자기 상태를 안정적으로 보존하지 못한다(세션 종료 = 상태 소멸).
- **커널 판정**: persona 격리 모델로 채택. 단 persona 는 **task 상태를 소유하지 않는다** — persona 는 stateless worker, 상태는 ledger.

### E. Workflow / State-machine (Temporal/Cadence durable execution, AWS Step Functions, LangGraph checkpointer)
- **상태 소유**: 워크플로 엔진의 이벤트 히스토리. 실패 후 히스토리 replay 로 재개.
- **장점**: long-horizon 신뢰성에서 가장 검증된 계열. replay·재시도·타임아웃이 1급 기능.
- **깨지는 조건**: 워크플로가 **사전에 코드로 고정**되어야 한다. 연구 task 는 중간에 계획이 바뀐다. 또한 Temporal 은 워크플로 코드의 결정성을 요구하는데, LLM 은 결정적이지 않으므로 "activity" 로 밀어내야 한다 — 이건 옳은 방향이지만 엔진 운영 비용이 크다.
- **커널 판정**: **개념(event history + deterministic replay + timeout)** 은 채택, **엔진** 은 지금 도입하지 않는다.

### F. Hybrid
- C 의 공유 기록 + E 의 결정적 상태기계/replay + D 의 persona 격리 + B 를 선택적 전송층으로.
- **비용**: 개념이 넷이라 설명이 어렵다. 그러나 구현은 오히려 가장 작을 수 있다 — 아래 커널은 파일 하나 + 순수 함수 하나다.

### 기준별 요약 (서술형)

| 기준 | A 중앙 | B Switchboard | C Blackboard | D Actor | E Workflow | F Hybrid (제안) |
|---|---|---|---|---|---|---|
| state ownership | LLM 맥락 | 없음(메시지만) | 공유 보드(가변) | actor 별 분산 | 엔진 히스토리 | append-only ledger, 규칙만 쓰기 허가 |
| failure isolation | 없음 | 라우터 SPOF | 보드 SPOF, persona 격리 | 강함 | 엔진 SPOF, activity 격리 | persona 격리, ledger 는 replay 복구 |
| context isolation | 없음(전부 한 창) | 강함 | 보드 전체 노출 | 강함 | 강함 | persona 는 task card(투영)만 봄 |
| credential isolation | 최악(전 권한 집중) | 라우터가 권한 없음 | persona 별 | persona 별 | worker 별 | 커널은 자격증명 0, persona 별 |
| auditability | 서술 | 메시지 로그 | 편집 가능 기록 | 분산 로그 | 강함 | hash-chain 이벤트, actor 귀속 |
| replay | 재실행만 | 불가 | 불가 | 부분 | 강함 | 상태 = fold(events), 결정적 |
| human gate | 프롬프트 규칙(우회 가능) | 외부 | 라벨 관례 | 외부 | signal/대기 | 규칙이 강제하는 이벤트 타입 |
| provider independence | orchestrator 모델에 묶임 | 높음 | 높음 | 높음 | 높음 | 높음(adapter 계약만) |
| cost | 토큰 최대(모든 것이 한 창 통과) | 낮음 | 낮음 | 중 | 운영비 큼 | 낮음 |
| complexity | 초기 최저, 규모에서 최고 | 낮음 | 낮음 | 중 | 높음 | 개념 중, 코드 최저 |
| long-horizon reliability | 맥락 한계에서 붕괴 | 해당 없음 | 동시성에서 붕괴 | 전체 진행 불명 | 강하지만 경직 | 가설(검증 대상) |

---

## MINIMUM KERNEL

브리프 예시의 7개(TASK ENVELOPE, STATE STORE, PLANNER, DISPATCH, PERSONA ADAPTER,
EVIDENCE VERIFIER, HUMAN GATE)를 하나씩 줄인다.

| 예시 컴포넌트 | 판정 | 이유 |
|---|---|---|
| TASK ENVELOPE | **흡수** → 이벤트 스키마 | envelope 는 컴포넌트가 아니라 데이터 형식 |
| STATE STORE | **유지** → Task Ledger | 없앨 수 없는 유일한 중심 |
| PLANNER | **제거** → persona 역할 | 커널 안의 planner 는 곧 중앙 추론자. 계획은 `plan.revise` 이벤트를 *제안*하는 역할일 뿐 |
| DISPATCH | **제거** → pull + lease | push 배정자가 있으면 그것이 orchestrator. persona 가 열린 step 을 claim 한다 |
| PERSONA ADAPTER | **커널 밖 계약** | 커널은 adapter 를 모른다. 이벤트 형식만 안다 |
| EVIDENCE VERIFIER | **분할** | 기계적 검사(해시·인용·저자≠검증자)는 규칙에, 의미 검증은 또 하나의 persona 역할 |
| HUMAN GATE | **흡수** → 규칙 | 게이트는 서비스가 아니라 "human principal 만 낼 수 있는 이벤트 타입" |

### 결과: 2 + 1

```
            (edge, 비결정적, 교체 가능)                      (core, 결정적, 지능 없음)
 ┌──────────────┐  propose(event)   ┌──────────────────────────────────────────┐
 │ Persona α    │ ────────────────▶ │  K2. ADMISSION RULES (pure function)     │
 │ (any model)  │                   │      admit(state, proposed) → ok | reject│
 └──────────────┘                   │                 │ ok                      │
 ┌──────────────┐  read task card   │                 ▼                         │
 │ Persona β    │ ◀──────────────── │  K1. TASK LEDGER (append-only, hash-chain)│
 └──────────────┘                   │      state = fold(reduce, events)         │
 ┌──────────────┐                   └──────────────────────────────────────────┘
 │ Human (HQ)   │ ── gate.* 이벤트 ──▶        (same path, human-only types)
 └──────────────┘
        ▲
        └─ K3. PERSONA CONTRACT: "task card 를 읽고, 이벤트 하나를 제안한다"
```

- **K1. Task Ledger** — append-only 이벤트 로그. 각 이벤트는 직전 이벤트 해시를 포함(hash chain).
  상태는 저장하지 않고 **언제나 계산한다**: `state = fold(reduce, events)`.
  단일 writer (한 task 당 한 ledger 파일). 분산 합의(Raft 등) 불필요.
- **K2. Admission Rules** — 순수 함수. 제안 이벤트를 현재 상태에 비추어 승인/거절.
  lease 소유, 수신 역할, 멱등성, 버전(stale), 스키마, 저자≠검증자, human-only 타입을 검사.
  **LLM 호출 없음.** 거절된 제안도 버리지 않고 별도 quarantine 로그에 남긴다(감사용).
- **K3. Persona Contract** — 커널 밖. "투영된 task card 를 받아, 서명된(귀속된) 이벤트 1개를 제안한다."
  사람이 무료 채팅 AI 에 카드를 붙여넣고 결과를 붙여넣는 것도 유효한 adapter 다.

Planner, dispatcher, verifier, gate, HQ snapshot, evidence pack 은
전부 **이 셋 위의 역할 또는 투영(projection)** 으로 표현된다. 커널에 넣지 않는다.

---

## WHY NOT CENTRAL SUPER-AGENT

1. **상태가 맥락에 산다.** 창을 넘거나 세션이 끊기면 task 가 사라진다. ledger 는 창 크기와 무관하다.
2. **요약은 검증 불가능한 원본 대체물이다.** orchestrator 가 "B 는 테스트를 통과했다"고 쓰면 그게 기록이 된다. 커널에서는 결과 이벤트 + 아티팩트 해시 + 검증 이벤트가 기록이고, 요약은 투영일 뿐이다.
3. **권한 집중.** 모든 도구를 배정하는 에이전트는 모든 자격증명을 가진다. 입력 하나의 prompt injection 이 전 시스템에 닿는다. 커널은 자격증명을 하나도 갖지 않는다.
4. **불일치의 평탄화.** 한 모델이 다른 AI 들의 결과를 "종합"하면 모순이 사라진다. AI CONSENSUS ≠ VERIFIED EVIDENCE 를 구조적으로 지킬 수 없다.
5. **Provider lock-in.** orchestrator 모델이 바뀌면 시스템 성격이 바뀐다.
6. **감사가 서술이 된다.** "왜 이렇게 됐나"의 답이 로그가 아니라 모델의 설명이다.
7. **Human Gate 가 프롬프트 규칙이 된다.** "승인 전에 실행하지 마라"는 문장은 우회될 수 있다. 커널에서는 규칙 함수가 거절한다.

단, A 는 **baseline** 으로 남긴다. 커널이 A 보다 느리고 비싸면서 신뢰성 이득이 없다면 H0 는 기각이다.

---

## EXISTING DREAM ASSET REUSE

§0 대로 아래 자산은 이 저장소에 없으므로 **설명된 역할 기준 조건부 판정**이다.

| 자산 | 판정 | 이유 | 주의(architecture contradiction) |
|---|---|---|---|
| **DREAM COM** (communication plane) | **ADAPT** | persona 에게 task card 를 전달하고 제안을 받아오는 **전송층**으로 적합 | 메시지 스트림이 사실상의 상태가 되면 안 된다. "전달됨"은 상태가 아니고 "ledger 에 승인됨"만 상태다. 재전송은 같은 idempotency key 로 |
| **PROJECT-002** (future execution plane) | **LATER** | 첫 실험은 실제 실행 금지. 커널은 PROJECT-002 에 의존하지 않는다 | 이후 연결 시 PROJECT-002 는 `gate.approve` 가 인용된 `exec.request` 이벤트만 소비해야 한다 (HANDOFF ≠ EXECUTION AUTHORIZATION) |
| **Knowledge Refinery** | **LATER** | 커널 작동에 불필요. task 종료 후 VERIFIED 결과를 지식으로 승격하는 하류 소비자 | 이 저장소의 `inbox → approved` 가 이미 그 승격 모양이다. 자동 승격 금지 유지 |
| **Evidence Pack** | **ADAPT** | ledger 구간(이벤트 + 아티팩트 해시 + 검증 체인)의 **내보내기 형식**으로 | Evidence Pack 이 원본이 되면 안 된다. ledger 에서 재생성 가능해야 한다 |
| **HQ Snapshot** | **ADAPT** (읽기 전용 투영) | `fold(events)` 결과를 보여주는 관측면 | HQ 는 control/observation plane 이지만 **planner 가 되면 안 된다**. HQ 가 쓰는 것은 human-only `gate.*` 이벤트뿐 |
| **Remote Adapter** | **LATER** | K3 계약만 지키면 어떤 adapter 든 된다. 첫 실험은 scripted/수동 adapter 로 충분 | adapter 는 persona 자격증명을 커널로 들여오면 안 된다 |
| **grok-knowledge-01 inbox 패턴** (실재) | **KEEP (선행 사례로)** | 사람만 붙이는 라벨 = human-only 이벤트, `vet-inbox.yml` = 결정적 admission 의 최소형 | GitHub 이슈는 편집·삭제 가능 → append-only 아님. ledger 로 쓰려면 hash-chain 이 추가로 필요 |

---

## STATE MODEL

### 이벤트 (ledger 의 한 줄)

```yaml
seq: 17                        # ledger 가 부여, 단조 증가
event_id: sha256(...)          # 아래 필드 + prev 의 해시
prev: <event_id of seq 16>     # hash chain
task_id: T-001
step_id: S-3                   # 없으면 task 수준
type: result.submit            # 아래 타입 목록 중 하나
actor:
  principal: persona | human | system
  persona_id: P-impl-2         # 역할이 아닌 인스턴스
  role: implementer
  provider: local-mock | <vendor> | human
  model: <model id or 'script'>
  adapter: manual-paste | script
expected_version: 16           # 제안자가 본 상태 버전 (optimistic concurrency)
lease_id: L-9                  # claim 으로 받은 lease (결과 제출 시 필수)
idempotency_key: P-impl-2:S-3:attempt-1
cites: [<event_id>, ...]       # 근거로 삼은 이벤트
artifacts:
  - path: out/parser.py
    sha256: ...
payload: { ... }               # 타입별 스키마
admitted_at: 2026-..           # ledger writer 의 시각 (제안자 시각 아님)
```

### 이벤트 타입 (최소 집합)

| 범주 | 타입 | 누가 |
|---|---|---|
| task | `task.create`, `task.close` | human (`close` 는 gate 필수) |
| 계획 | `step.open`, `step.cancel`, `plan.revise` | persona(planner 역할) 또는 human |
| 작업권 | `step.claim`, `step.release`, `lease.expire` | persona / system(시간 경과 판정) |
| 결과 | `result.submit` | lease 보유 persona |
| 검증 | `verify.accept`, `verify.reject` | 저자가 아닌 persona 또는 deterministic check |
| 불일치 | `dispute.open`, `dispute.resolve` | 누구나 open, resolve 는 규칙/사람 |
| 게이트 | `gate.request`, `gate.approve`, `gate.deny`, `policy.grant` | request 는 누구나, 나머지 **human only** |
| 연속성 | `checkpoint` | persona — 반드시 `cites` 포함, 자체도 검증 대상 |

### Step 상태기계

```
OPEN ──claim──▶ CLAIMED(lease) ──submit──▶ SUBMITTED ──accept──▶ VERIFIED ──(필요시) gate──▶ DONE
  ▲                 │                          │
  └──expire/release─┘                          ├──reject──▶ OPEN (재작업, 이전 결과 보존)
                                               └──conflicting accept/reject──▶ DISPUTED ──resolve──▶ VERIFIED | OPEN
                                                                                   └──unresolvable──▶ BLOCKED(awaiting human)
```

### 불변식 (Invariants) — 실험에서 매 이벤트마다 검사
- **I1** 상태는 오직 `fold(events)` 로만 존재한다. 다른 저장된 상태는 캐시이며 불일치 시 캐시가 틀린 것이다.
- **I2** `result.submit` 은 현재 유효 lease 보유자만 가능하다.
- **I3** 같은 `idempotency_key` 는 최대 1회 승인된다.
- **I4** `expected_version` 이 해당 step 의 마지막 변경보다 오래되면 거절(STALE).
- **I5** `verify.*` 의 actor ≠ 해당 result 의 actor.
- **I6** `gate.*`, `policy.grant`, `task.close` 는 principal=human 만.
- **I7** hash chain 이 끊기면 ledger 전체를 신뢰하지 않는다(append 중단, 사람 호출).
- **I8** 거절된 제안은 quarantine 로그에 남고 절대 조용히 사라지지 않는다.

---

## HANDOFF MODEL

**Handoff = `step.open` 이벤트.** 메시지가 아니다.

```yaml
type: step.open
payload:
  goal: "insight-room:v1 블록 파서 구현"
  to_role: implementer          # 기본: 역할 지정 → 자격 있는 누구나 claim
  to_persona: null              # 선택: 특정 인스턴스 지정(directed)
  inputs: [<event_id>, <artifact sha256>]   # 참조만. 복사된 요약 아님
  acceptance:                   # 가능한 한 기계 검사 가능하게
    - "tests/test_parser.py 전부 통과"
    - "blocked 용어 목록은 vet-inbox.yml 과 동일"
  lease_ttl: 30m
  budget: { max_attempts: 3 }
  authority: propose            # read | propose  — execute 는 존재하지 않는다
```

- **Pull, not push.** persona 가 열린 step 을 보고 `step.claim` 한다. 규칙이 역할을 확인하고 lease 를 준다.
- **HANDOFF ≠ EXECUTION AUTHORIZATION.** step 의 `authority` 에는 `execute` 가 없다. 효과가 있는 행동은 `gate.approve` 를 `cites` 한 별도 이벤트로만 요청할 수 있고, 그 소비자(PROJECT-002 등)는 이 실험 범위 밖이다.
- **COMMUNICATION ≠ AUTHORITY.** DREAM COM 으로 카드가 도착해도 그것은 알림이다. claim 이 승인되기 전에는 아무 권한이 없다.
- **Task card** = persona 가 받는 유일한 입력. ledger 에서 **결정적으로 생성**되는 투영:
  task 목표, 현재 step, acceptance, 인용된 이벤트/아티팩트 원문, 최근 checkpoint, 열린 dispute.
  크기 상한을 둔다. 상한을 넘으면 새 `checkpoint` 가 필요하다 — 이게 Top Unknown #1.

---

## EVIDENCE MODEL

증거 수준을 서열로 둔다. 상위 수준은 하위 수준의 모든 조건을 포함한다.

| 수준 | 조건 | 예 |
|---|---|---|
| **E0 CLAIM** | persona 가 말했다 | "테스트 통과했습니다" |
| **E1 ATTESTED** | 아티팩트 해시가 ledger 에 있고, 재현 명령이 기록됨 | `sha256`, `cmd: pytest -q`, 출력 해시 |
| **E2 VERIFIED** | 저자가 아닌 주체가 **재실행/재도출** 하여 일치 — deterministic check 또는 다른 persona(가능하면 다른 provider) | 검증자가 같은 커밋에서 테스트 재실행, 출력 해시 일치 |
| **E3 HUMAN-ACCEPTED** | E2 + human `gate.approve` 가 해당 이벤트를 cite | task 종료 |

규칙:
- **동의 ≠ 검증.** N 개의 AI 가 결과를 "검토하고 동의"했지만 재실행/재도출이 없으면 여전히 **E0** 다. 같은 학습 데이터를 공유한 모델들의 오류는 상관되어 있다.
- **모순은 보존한다.** `verify.accept` 와 `verify.reject` 가 공존하면 step 은 DISPUTED. 다수결·평균 금지.
- **해소 순서:** (1) 기계 검사 가능한 acceptance 로 판정 → (2) 새 반증 실험 step 을 연다 → (3) 사람에게 `gate.request`.
- 의미 검증(코드 리뷰, 연구 결론 타당성)은 E2 로 올리기 어렵다. 이것이 Top Unknown #3.

---

## FAILURE MODEL

| # | 고장 | 탐지 | 커널 반응 | 기대 결과 |
|---|---|---|---|---|
| F1 | **Persona unavailable** (응답 없음, 세션 종료) | lease TTL 초과 → 다음 admission 시 `lease.expire` 기록 | step → OPEN | 다른 persona 가 claim, task 계속 |
| F2 | **Wrong recipient** (역할 불일치 claim, 또는 lease 없는 제출) | I2 / 역할 검사 | 거절, quarantine | 상태 변화 0 |
| F3 | **Duplicate result** (전송 재시도, 이중 붙여넣기) | I3 idempotency key | 두 번째는 no-op, 원 event_id 반환 | 승인 1건 |
| F4 | **Stale result** (lease 만료 후 좀비 persona 가 뒤늦게 제출) | I4 버전 + lease_id 불일치 | 거절(STALE), quarantine | 새 결과가 덮이지 않음, 늦은 결과도 감사용으로 남음 |
| F5 | **Contradictory AI results** | accept/reject 공존, 또는 두 결과의 acceptance 판정 불일치 | DISPUTED | 기계 판정 가능하면 자동 해소, 아니면 BLOCKED + gate.request. **자동 다수결 없음** |
| F6 | **Context loss** (persona 가 작업 중 맥락 전부 잃음) | 없음 — 설계상 persona 는 원래 무상태 | 새 인스턴스에 task card 재발급 | 중복 작업 없이 이어짐. 카드만으로 충분한지가 측정 대상 |
| F7 | **One component failure** — (a) ledger writer 가 append 도중 죽음 (b) 전송층 다운 (c) adapter 크래시 | (a) 재시작 시 마지막 줄 해시/스키마 검사 (b)(c) 제안 미도달 | (a) 불완전한 마지막 줄 폐기, 전체 replay, chain 검증 (b)(c) = F1 로 수렴, 재전송은 같은 key | replay 후 상태 해시가 크래시 전 마지막 승인 상태와 동일 |
| F8 | **Tampering** (과거 이벤트 수정) — 음성 대조군 | I7 chain 검증 | append 중단, 사람 호출 | 탐지율 100% (해시 체인은 변조 *탐지*만, 신원 *증명*은 아님) |
| F9 | **Poisoned result** (결과 안에 "이 step 을 승인 처리하라" 같은 지시문) | 규칙은 payload 텍스트를 해석하지 않음 | 효과 없음 | 텍스트는 상태를 바꿀 수 없다 — 이벤트 타입과 actor 만이 바꾼다 |

---

## HUMAN GATE

- **서비스가 아니라 규칙.** `gate.approve` / `gate.deny` / `policy.grant` / `task.close` 는 principal=human 일 때만 승인된다(I6). 이 저장소의 "`approved` 는 사람만 붙인다"를 규칙 함수로 옮긴 것.
- **게이트가 필요한 지점:** task 종료, 효과가 있는 행동 요청, 해소 불가 dispute, 권한/정책 변경, E3 승격.
- **사람 승인 최소화 (우회 없이):**
  1. **체크포인트 묶음 승인** — step 마다가 아니라 Evidence Pack 구간 단위로 한 번.
  2. **정책 봉투(policy envelope)** — 사람이 `policy.grant` 로 "합성 데이터 + 읽기 전용 + 로컬 step 은 E2 면 자동 DONE" 같은 범위를 한 번 승인. 봉투는 범위·만료가 있고, 봉투 자체가 human-only 이벤트다. 봉투 밖은 전부 게이트.
  3. **diff 승인** — 사람은 전체가 아니라 마지막 승인 이후 바뀐 E2 결과만 본다.
- **모순 지적:** 첫 실험은 "credential 없음" 이므로 human principal 의 신원은 **자기 선언**이다. 실험은 규칙이 human-only 타입을 강제하는지만 검증하고, 사람이 진짜 사람인지는 검증하지 못한다. 이 한계를 결과 보고에 명시해야 한다.

---

## FIRST EXPERIMENT

### EXP-PRD-001-A "Relay Survival"

**반증하려는 가설:** 2+1 커널(ledger + admission rules + persona contract)만으로,
하나의 task 가 4 개 이상의 persona handoff 와 F1–F9 고장을 거치면서도
state / evidence / identity attribution / recovery 를 유지한다.

**제약 준수:** production 없음 · credential 없음 · 유료 provider 불필요 · PROJECT-002 실제 실행 없음 · 외부 게시 없음 · 네트워크 없음.

**Task (합성이지만 실제 엔지니어링):**
이 저장소의 `vet-inbox.yml` 판정 로직을 로컬 순수 함수로 옮기고 테스트한다.
→ 결과물이 기계 검사 가능한 acceptance 를 갖는다 (E2 가 실제로 가능).

```
S1 spec      (role: analyst)      → 판정 규칙 명세 (blocked 용어, 필수 마커 4개)
S2 implement (role: implementer)  → 파서/판정 함수
S3 test      (role: tester)       → 합성 이슈 본문 fixture + 테스트
S4 verify    (role: reviewer)     → S2+S3 재실행, 저자≠검증자
S5 gate      (human)              → gate.approve → task.close
```

**Personas:** 4 역할 × 인스턴스 2개씩 = 8 개의 scripted persona (결정적 스크립트, provider=`local-mock`).
각 persona 는 task card 만 입력으로 받는다(프로세스 간 공유 메모리 금지).

**Arm B (선택, 무료):** 한 역할(implementer)을 사람이 무료 채팅 AI 에 task card 를 붙여넣는 manual adapter 로 교체.
scripted persona 는 커널을 시험하고, Arm B 는 "카드만으로 실제 LLM 이 이어갈 수 있는가"를 처음으로 건드린다.

**구현 규모 상한 (후속 LOT 용):** Python 표준 라이브러리만, JSONL ledger 파일 1개, 순수 함수 `reduce`/`admit`, 단일 프로세스 시뮬레이터 + 고장 주입기. 목표 600 줄 이하.

**실행 행렬:**
1. Baseline — 고장 없음.
2. 단일 고장 — F1…F9 각각 1회, 지정된 step 에 주입.
3. 복합 — 시드 고정 랜덤 고장 스케줄 200개 (각 스케줄에 고장 1–4개).
4. Baseline-A 비교 — 같은 task 를 "orchestrator 가 모든 상태를 한 텍스트 요약으로 보관" 하는 모의 구현으로 수행하고, 같은 F6(맥락 소실)·F4(stale) 를 주입. 커널의 이득이 실제로 있는지 대조.

**측정:**
- task 종료율 / BLOCKED 비율과 사유
- 불변식 I1–I8 위반 수
- 승인·거절·quarantine 이벤트 수 (고장별)
- replay 상태 해시 일치 여부
- task card 크기 (step 별, 최대값) — 커널의 확장성 신호
- handoff 당 추가 이벤트 수 (오버헤드)

---

## SUCCESS CONDITION

실험은 다음을 **모두** 만족할 때만 성공이다. 하나라도 실패하면 H0 는 수정 또는 기각.

1. Baseline 과 F1–F4, F6, F7 시나리오에서 task 가 `task.close`(human gate 포함)에 도달.
2. F5 시나리오에서 task 는 **자동 해소되지 않거나**, 기계 판정 가능한 acceptance 로만 해소된다. 다수결 해소 0건.
3. 모든 시나리오 후 `fold(ledger)` 를 처음부터 재계산한 상태 해시 = 실행 중 상태 해시.
4. F8 변조 탐지 100%, 그리고 변조 후 append 0건.
5. 복합 200 스케줄에서 불변식 위반 0건.
6. 승인된 모든 `result.submit` 에 actor 1개 + 유효 lease 1개. 비 lease 보유자의 결과 승인 0건.
7. F3 → 승인 정확히 1건. F4 → 승인 0건, quarantine 1건.
8. 모든 VERIFIED step 에서 검증자 ≠ 저자, 최종 산출물 테스트 통과(E2).
9. task card 최대 크기가 step 수에 대해 **선형 이하**로 유지(checkpoint 사용 시). 선형 이상으로 자라면 long-horizon 가설 기각 신호.
10. Baseline-A 대비: F6·F4 에서 A 는 상태 손상/덮어쓰기가 재현되고 커널은 재현되지 않아야 한다. 둘이 같다면 커널의 복잡도는 정당화되지 않는다.

**명시적 한계 (성공해도 증명되지 않는 것):**
scripted persona 로 성공해도 "실제 LLM 이 카드만으로 장기 task 를 이어간다"는 증명되지 않는다.
attribution 은 자기 선언이므로 "신원 보존"은 **일관성**까지만 검증된다.

---

## WHAT NOT TO BUILD

- 커널 안의 planner / dispatcher / scheduler (그 순간 orchestrator)
- 중앙 요약 에이전트, "memory" 에이전트
- 벡터 DB 장기 기억
- DREAM COM 연동, PROJECT-002 연동, Remote Adapter 연동 (첫 실험에서)
- 인증/자격증명 시스템, 키 관리
- 합의 투표·신뢰 점수
- 대시보드 / HQ UI
- Temporal 등 워크플로 엔진 도입
- 다중 task 동시성, 분산 ledger, 합의 프로토콜
- Knowledge 자동 승격, `approved` 자동 부여
- 어떤 형태의 외부 게시·메시징

---

## TOP 3 UNKNOWN

1. **카드 연속성 (card continuity).** 실제 LLM persona 가 bounded task card 만으로 수십~수백 step 을 이어갈 수 있는가? checkpoint 요약이 반복되면 "요약의 요약"이 사실을 잃는다(summary rot). cites 의무화가 이를 막는지, 막으려면 카드가 얼마나 커지는지 모른다.
2. **자격증명 없는 귀속 (attribution without credentials).** `actor` 필드는 자기 선언이다. provider 는 출력에 서명하지 않는다. adapter 서명은 "이 adapter 가 전달했다"만 증명한다. persona 신원을 provider 출력에 묶는 방법과, 그 방법이 credential isolation 을 깨지 않는지는 미해결.
3. **의미 검증의 상한 (semantic verification ceiling).** 기계 검사 가능한 acceptance 가 없는 연구 결론·설계 판단에서 무엇을 E2 로 볼 것인가? 서로 다른 모델 간 동의는 오류가 상관되어 있어 약한 증거다. 이 경계가 정해지지 않으면 연구 task 는 대부분 E0/E1 에 머물고 게이트 부담이 사람에게 쏠린다.

---

## NEXT SINGLE RESEARCH LOT

**CLAUDE-PRD-002 — Task Ledger Kernel Prototype + Fault Harness**

- 범위: EXP-PRD-001-A 의 구현과 실행만. Arm B 는 HQ 가 별도 허가할 때만.
- 산출: (1) 로컬 prototype (Python stdlib, ≤600 줄, 네트워크 없음) (2) F1–F9 + 200 시드 결과 표 (3) replay 해시 증거 (4) Baseline-A 대조 결과 (5) §SUCCESS CONDITION 항목별 PASS/FAIL 과 원시 로그 해시.
- 금지: §7 AUTONOMY BOUNDARY 전부 유지. main 병합 없음. 외부 호출 없음.
- 종료 조건: SUCCESS CONDITION 10개 판정 완료 시. 실패 항목이 있으면 수정 설계를 하되 재구현은 다음 LOT 로.

---

## 부록: 이 LOT 에서 찾은 설계상 모순 (architecture contradiction log)

| # | 모순 | 해소 |
|---|---|---|
| C1 | "중앙 super-agent 금지" vs 예시 컴포넌트에 PLANNER·DISPATCH | 둘 다 커널에서 제거. 계획은 제안 역할, 배정은 pull+lease |
| C2 | "HQ = CONTROL plane" vs "중앙 없음" | HQ 의 control 은 *정책과 게이트* 이지 *계획* 이 아니다. HQ 는 human-only 이벤트만 쓴다 |
| C3 | DREAM COM = communication plane 인데, 여러 plane 을 "하나의 OS 처럼" 보이게 하려면 메시지 로그가 상태가 되기 쉽다 | 상태는 ledger 에만. DREAM COM 은 전달, "도착" ≠ "승인" |
| C4 | "Human approval minimization" vs "no Human Gate bypass" | 최소화는 사람이 승인한 범위·만료 있는 policy envelope 로만 |
| C5 | 실험 요구 "identity attribution 보존" vs "credential 없음" | 실험은 귀속 **일관성** 만 검증. 진위는 Top Unknown #2 |
| C6 | "기존 자산 재사용 먼저" vs 해당 자산이 접근 가능한 저장소에 없음 | 조건부 판정으로 표기. HQ 가 자산 스펙 위치를 주면 재판정 |
