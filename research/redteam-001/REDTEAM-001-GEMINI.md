# DREAM EXECUTION / EVIDENCE RED-TEAM-001 — Gemini R&D-001 독립 검증

2026-09-28 · Claude Code · 대상: `Execution_and_Evidence_RD_Report.md` (Gemini)
금지 준수: 구현 없음, Production·Main 수정 없음, Provider 호출 없음, Browser 실행 없음.

## 검증 근거

| 등급 | 내용 |
|---|---|
| **DOC-VERIFIED** | 2026-09-28 GitHub/Playwright 공식 문서 확인. 이 환경은 `docs.github.com` 직접 접속이 차단되어 Exa로 읽음. 대상: Secure use reference, Variables reference, Deployments and environments, Events that trigger workflows, Actions billing, Artifact retention, Playwright Trace viewer |
| **PROBE** | `gemini-autopromotion-probe.mjs` (이번 라운드), `probes.mjs` P1–P4와 P5·P6 (직전 라운드, `REDTEAM-001.md`) |
| **INFERRED** | 문서로 확인하지 못한 추론. 판정에 그대로 표시 |
| **UNKNOWN** | 사용자의 GitHub 플랜, 협업자 수, 2번 저장소 내용, `BROWSER-LOCAL-001`·`verify-browser.mjs` 존재 여부 |

## CRITICAL RISKS

| # | 위험 | 근거 |
|---|---|---|
| **C1** | **State Auto-Promotion이 HOLD·실패·위조 결과를 승격한다.** 규칙 `executionStatus==='SUCCESS' && realStateChanged===false`를 그대로 적용하면 다음 셋이 모두 **PROMOTED**: G1 Refinery가 HOLD로 정상 종료, G2 assertion 2개 실패인데 wrapper가 exit 0, G3 PR에서 runner 스크립트를 고쳐 자기신고 envelope을 씀. Gemini의 `executionStatus`에는 HOLD도 테스트 판정도 없어서 **"프로세스가 끝났다"가 "통과했다"로 바뀐다** | PROBE G1–G3 |
| **C2** | **Authority가 workflow 입력값이라 위조 가능하다.** §7에서 `workflow_dispatch`로 `authority`를 넘긴다. dispatch할 수 있는 사람은 R2를 입력할 수 있다. 문서상 쓰기 권한자는 workflow를 실행할 수 있고, 저장소 secret도 전부 읽을 수 있다 | DOC (Secure use, Billing TIP) |
| **C3** | **Trace ZIP 업로드는 자격증명 유출이다.** trace에는 요청 헤더·본문과 쿠키가 저장된다(Playwright 문서 Network 탭, P6 실측: Bearer 토큰과 세션 쿠키 평문). 게다가 Playwright 공식 CI 권장 설정이 `retries: 1` + `trace: 'on-first-retry'`다. **기본값을 따르면 재시도와 trace가 동시에 켜진다** | DOC + PROBE P6 |
| **C4** | **Human Gate가 protected environment에 기대는데, private repo에서는 쓸 수 없다.** 문서: "If you are on a GitHub Free, GitHub Pro, or GitHub Team plan, required reviewers are only available for public repositories." wait timer와 관리자 우회 금지도 같다. Free에서는 private repo의 environment secret 자체가 없다 | DOC (Deployments and environments) |
| **C5** | **Runner → DREAM CONTROL webhook POST**에는 runner 안에 DREAM CONTROL 자격증명이 있어야 하고, 받는 쪽은 자기신고 JSON을 믿게 된다. 새 비밀 하나와 새 공격면 하나가 생긴다 | INFERRED (구조) |
| **C6** | **AI Provider key의 PR 유출.** fork PR에는 secret이 전달되지 않지만(DOC), **같은 저장소 브랜치의 PR**은 `pull_request`로 secret을 받는다(INFERRED, 문서에 fork 예외만 명시). DREAM은 AI가 브랜치를 push하는 구조라서, AI나 오염된 의존성이 PR에서 workflow를 고쳐 key를 빼낼 수 있다. Gemini의 "main에서만 AI 실행"은 **PR 쪽 workflow가 secret을 참조할 수 없게 막아야** 성립한다 | DOC + INFERRED |
| **C7** | **`runId` 하나로는 idempotency가 안 된다.** `GITHUB_RUN_ID`는 "does not change if you re-run", `GITHUB_RUN_ATTEMPT`만 증가한다. 입력으로 받는 runId는 위조되거나 충돌할 수 있다. timeout으로 job이 죽으면 evidence가 **아예 쓰이지 않고**, provider 요청이 이미 나갔다면 결과는 OUTCOME_UNKNOWN이다. 이때 재전송하면 중복 과금이나 중복 게시가 된다. 중복 제거 저장소도 없다(P1: 메모리 idempotency는 재시작 후 재실행) | DOC + PROBE P1 |
| **C8** | **"GH Actions is effectively free"는 틀렸다.** private repo는 Free 2,000분/월, 500MB 저장이다. 초과분은 Linux 2-core 기준 $0.006/분이고 저장은 시간당 누적된다. 쓰기 권한자 누구나 소유자 분량을 소모하며, 실패 후 재실행은 **두 번 과금**된다 | DOC (Billing) |
| **C9** | **Evidence를 PASS로 오인할 경로 4개.** ① `SUCCESS`를 PASS로 읽음 ② `realStateChanged: boolean`은 자기신고라 상수로도 false가 나온다(P3) ③ 소스 SHA가 없다. PR에서 `GITHUB_SHA`는 head가 아니라 **merge commit**(DOC) ④ `runnerIdentity` 문자열은 자기신고이고, `RUNNER_NAME`은 "may not be unique"(DOC) | DOC + PROBE P3 |
| **C10** | 이 레인의 연구물이 public 저장소 브랜치에 있다(이전 D8, 미결) | 사실 |

## 제안별 판정 (Gemini 원문 순서)

| # | Gemini 제안 | 판정 | 이유 · 최소 대안 |
|---|---|---|---|
| 1.1 | GitHub Actions를 실행 샌드박스로 | **KEEP** | GitHub-hosted runner는 ephemeral VM이다(DOC). 신원(identity)은 OIDC가 아니라 **HQ가 API로 읽는 run 기록**으로 충분하다. OIDC는 클라우드 자격증명이 생길 때까지 불필요 |
| 1.2 | Playwright + 작은 DREAM wrapper | **SIMPLIFY** | wrapper 없이 `@playwright/test` 설정으로 끝낸다. `retries: 0`, `trace: 'off'`, 스크린샷만. 공식 CI 기본값(재시도 1 + trace)을 반드시 덮어쓴다 |
| 1.3 | MCP (실험) | **REJECT (지금)** | Provider 호출이 금지 상태이고, 도구 노출 면만 늘어난다. Provider runner가 승인될 때 다시 연다 |
| 1.4 | n8n 사용 안 함 | **KEEP** | 단, 대안으로 적은 "GitHub Webhook → DREAM CONTROL"은 REJECT (4.1) |
| 1.5 | Temporal 사용 안 함 | **KEEP** | 단, "Minimum Contract의 atomic idempotency key"는 필드일 뿐 원자성이 아니다 (C7) |
| 1.6 | OTel/SLSA 개념만 | **SIMPLIFY** | provenance 6필드만 쓴다: repo, head_sha, tested_sha, workflow_ref, run_id, run_attempt. attestation 기능의 private repo 가용성은 UNKNOWN이므로 의존하지 않는다 |
| 2 | ExecutionContract (별도 JSON 지시서) | **REJECT (문서로서)** | **workflow 파일 자체가 실행 계약이다.** `GITHUB_WORKFLOW_SHA`가 계약 버전이다. 별도 지시서는 위조 가능한 입력만 늘린다 |
| 2.a | `runId` | **REJECT** | `run.id` + `run.attempt`를 GitHub가 부여한다 (C7) |
| 2.b | `identity` | **REJECT** | 자기신고다. `github.actor`/`triggering_actor`를 API로 확인 (re-run은 원래 actor 권한으로 실행됨, DOC) |
| 2.c | `authority` 입력 | **REJECT** | C2. Authority는 **job이 닿을 수 있는 자격증명**으로 정해진다(§SAFE BOUNDARY) |
| 2.d | `target` enum | **SIMPLIFY** | runner 종류마다 workflow 파일 하나. 파일 이름이 target이다 |
| 2.e | `immutableInput` (hash) | **KEEP → SIMPLIFY** | `input_hash` 하나만 남긴다. `prompts: string[]`를 evidence에 싣는 것은 REJECT (prompt 유출) |
| 2.f | `timeoutMs` | **SIMPLIFY** | `timeout-minutes` |
| 2.g | `allowNetwork` | **EXPERIMENT_REQUIRED** | GitHub-hosted runner에는 기본 egress 차단이 없다(DOC는 채굴 풀 hosts 차단만 언급). 강제 수단 없이 true/false 필드만 두면 안전 착시다 |
| 2.h | `maxCostUsd` | **EXPERIMENT_REQUIRED** | runner는 호출 전에 실제 비용을 모른다. 실효 상한은 provider 콘솔의 지출 한도와 요청별 `max_tokens`. Provider 호출 승인 후 검증 |
| 3 | EvidenceContract | **SIMPLIFY** | 아래 MINIMUM EVIDENCE CONTRACT로 대체 |
| 3.a | `executionStatus` 4값 | **REJECT → 분리** | 실행·권한·판정이 한 enum에 섞였고 HOLD와 OUTCOME_UNKNOWN이 없다(§6 본문과도 모순). 축 3개로 나눈다 |
| 3.b | `runnerIdentity` 문자열 | **REJECT** | C9-④ |
| 3.c | `rawResult: any` | **SIMPLIFY** | 판정이 아니라 artifact다. 판정은 `checks[]` |
| 3.d | artifact `sha256` | **KEEP (조건부)** | runner가 계산한 hash는 자기신고다. **HQ가 수집 시점에 재계산해 기록**할 때만 변조 탐지가 된다. `TRACE_ZIP`은 REJECT (C3). `AI_RAW_LOG`는 REJECT (prompt·PII) |
| 3.e | `realStateChanged: boolean` | **REJECT → SIMPLIFY** | `{changed, method, negative_control}`. 측정하지 않았으면 `null` + NOT_MEASURED (P3) |
| 3.f | `costIncurredUsd: number` | **REJECT → SIMPLIFY** | job 안에서 분 단위 청구액을 알 수 없다. `{kind: ACTUAL\|ESTIMATE\|UNKNOWN, usd, basis}`. 기본값은 UNKNOWN이고 0이 아니다 |
| 3.g | `externalCallsCount` | **EXPERIMENT_REQUIRED** | 셀 수단이 없으면 NOT_MEASURED |
| 4.1 | GHA → Webhook POST → DREAM CONTROL | **REJECT** | C5. **HQ가 GitHub API로 pull**한다. runner에는 비밀이 0개 |
| 4.2 | State Auto-Promotion | **REJECT** | C1. 대안은 SAFE AUTOMATION BOUNDARY의 **Promotion Proposal** |
| 4.3 | trace.playwright.dev 임베드 | **REJECT** | `?trace=URL`은 CORS로 접근 가능한 저장소가 필요하다(DOC). private artifact를 쓰려면 trace를 외부로 재호스팅해야 하고, trace에는 자격증명이 있다 (C3) |
| 5.1 | R1→R2 서명/기록된 사람 승인 | **KEEP (개념) / SIMPLIFY (구현)** | required reviewers는 private repo에서 사용 불가(C4). **R2는 CI가 실행하지 않는다. 사람이 CI 밖에서 직접 수행한다** |
| 5.2 | EXPLAIN_HOLD는 사람이 해소 | **KEEP** | |
| 6 | 자체 CI·큐·trace viewer·AI 자동 재시도 루프·거대 API Gateway 금지 | **KEEP** | 추가로 Playwright `retries` 기본 권장값도 금지 대상에 넣는다 |
| 7 | First Lot (`verify-twin.yml`, runId·authority 입력, trace zip 업로드) | **SIMPLIFY** | 입력 2개와 trace를 제거한다. 대상 경로 `hq/dream-control/browser-harness/verify-browser.mjs`와 BROWSER-LOCAL-001은 **존재 NOT_VERIFIED**. 2번의 **실제 UI**를 대상으로 한다 (FIRST LOT) |
| 8.1 | 비용 "Minimal / effectively free" | **REJECT** | C8 |
| 8.2 | 관리 15분 → 30초 | **EXPERIMENT_REQUIRED** | 측정값이 아니라 추정이다. FIRST LOT에서 실측 |
| 9.1 | AI key 보호 (main 한정 또는 PR 승인) | **EXPERIMENT_REQUIRED (이번 LOT 제외)** | Pro/Team이면 environment의 deployment branch를 `main`으로 제한할 수 있다(DOC). Free는 private repo environment secret이 없다. 승인자 기능은 없다 (C4). 플랜 UNKNOWN |
| 9.2 | S3 장기 보관 | **REJECT (지금)** | R2 실행 기록이 아직 없다. private repo 보존 기간은 최대 400일까지 설정 가능하다(DOC) |

## 질문별 판정 요약

1. **Execution ≠ Evaluation ≠ Promotion — 분리 필수.** 한 enum으로 합치면 C1이 생긴다. Promotion은 사람이 결정하는 **세 번째 축**이다.
2. **Authority** — runner 입력 하나로 위조 가능하다(C2). **Site는 자체적으로 재검증해야 한다(필수).** 다만 그 방법은 필드 검사가 아니라 **자격증명 부재**다. R2 자격증명이 CI에 없으면 어떤 입력으로도 R2가 불가능하다. 환경변수(`CI=true` 등)로 거부하는 방식은 우회되므로 보조 수단일 뿐이다.
3. **Idempotency** — runId만으로는 부족하다(C7). R1에는 실제 부수효과가 없으므로 중복 실행이 무해하고, 이것이 R1을 유지할 이유다. **Provider 호출은 과금이라는 부수효과가 있으므로 R1이 아니다.** OUTCOME_UNKNOWN은 절대 자동 재전송하지 않는다.
4. **Actions 보안** — 최소 안전구조는 FIRST LOT의 workflow다. `pull_request_target`은 금지한다(DOC: 신뢰할 수 없는 checkout과 결합하면 저장소 탈취). manual approval과 protected environment는 private repo 플랜에서 대부분 불가(C4).
5. **Evidence 무결성** — screenshot, trace, rawResult는 **PASS 증거가 아니라 보조 자료**다. PASS 판정 근거는 다음 셋이다: 알려진 SHA의 assertion 코드가 만든 `checks[]`, GitHub가 기록한 job 결론, HQ가 수집 시 재계산한 hash. `result_hash`를 runner가 자기서명하는 것은 불필요하다.
6. **Cost** — ACTUAL / ESTIMATE / UNKNOWN 구조가 필요하다. 0 추정은 금지한다.
7. **Failure semantics** — 분리가 필요하다. 특히 **TIMED_OUT과 OUTCOME_UNKNOWN은 runner가 스스로 쓸 수 없다.** 죽은 job은 evidence를 남기지 못하므로 HQ가 "evidence 없음 + job 결론"으로 도출한다. evidence가 없으면 NOT_MEASURED이지 PASS가 아니다.
8. **Admin 자동화** — Evidence Packet 자동 생성은 허용한다. 승격, 재시도, Production 변경은 불허한다(SAFE BOUNDARY).
9. **구조 축소** — 더 단순한 구성은 로컬 실행이지만 그러면 run 신원이 자기신고가 된다. GitHub Actions의 가치는 **제3자가 기록한 실행 신원**이므로 유지한다. Temporal, n8n, 자체 큐, API Gateway, 중앙 Execution Platform은 **모두 불필요**하다. 오케스트레이션할 R2 작업이 없고, GitHub가 스케줄·타임아웃·보관·기록을 이미 제공한다. JSON 계약도 2개가 아니라 **1개**(Evidence)로 충분하다.

## KEEP

GitHub-hosted Actions (실행 신원과 보관) · Playwright Test (설정만) · n8n / Temporal / 자체 큐 / Gateway 금지 · AI 자동 재시도 금지 · EXPLAIN_HOLD는 사람이 해소 · R2는 사람이 하는 개념 · `input_hash` · HQ가 재계산하는 artifact sha256

## SIMPLIFY

- ExecutionContract → workflow 파일 1개
- EvidenceContract → 아래 1개 스키마
- executionStatus → 3축
- `realStateChanged` → negative control 포함
- `costIncurredUsd` → ACTUAL / ESTIMATE / UNKNOWN
- `timeoutMs` → `timeout-minutes`
- `target` → workflow 파일 이름
- SLSA → provenance 6필드
- Human Gate → CI 밖의 사람 실행

## REJECT

State Auto-Promotion · authority/runId/identity 입력 · webhook POST · trace ZIP 업로드와 trace.playwright.dev 임베드 · AI_RAW_LOG/prompt를 evidence에 싣는 것 · `runnerIdentity` 문자열 · "비용 무료" · MCP(지금) · S3(지금) · 별도 ExecutionContract 문서

## EXPERIMENT_REQUIRED

`allowNetwork` 강제 수단 · `maxCostUsd` 실효성 · `externalCallsCount` 측정 · 관리시간 절감 실측 · AI key 보호 구조(플랜 확인 후)

## MINIMUM EXECUTION CONTRACT

**workflow 파일 1개가 곧 계약이다.** 규칙 8개:

1. 트리거는 `pull_request`(같은 저장소)와 `workflow_dispatch`뿐이다. **`pull_request_target`, `workflow_run`은 금지.**
2. `permissions: contents: read`만 허용한다. `secrets.*` 참조 0개. `actions/checkout`에 `persist-credentials: false`.
3. 외부 action은 전체 commit SHA로 고정한다(DOC 권장). `.github/workflows/`는 CODEOWNERS 대상으로 둔다(강제 여부는 플랜에 따라 UNKNOWN).
4. `timeout-minutes: 10`, `concurrency`로 같은 ref 중복 실행을 취소한다.
5. Playwright는 `retries: 0`, `trace: 'off'`, 스크린샷만 허용한다. 인증이 필요 없는 R1 화면만 대상으로 한다.
6. 입력 인자 0개. authority, runId, identity는 받지 않는다.
7. 판정의 진실은 exit code다. 모든 check가 PASS일 때만 0.
8. `evidence.json`과 스크린샷을 artifact로 올리고(retention 14일), 요약을 `$GITHUB_STEP_SUMMARY`에 쓴다.

## MINIMUM EVIDENCE CONTRACT

```json
{
  "schema": "dream.evidence.v0",
  "factory": "F02",
  "source": { "repo": "", "head_sha": "", "tested_sha": "", "workflow_ref": "" },
  "run": { "id": 0, "attempt": 1, "event": "pull_request", "actor": "", "runner_environment": "github-hosted" },
  "input_hash": "sha256:…",
  "execution": "COMPLETED",
  "evaluation": "PASS | PATCH | HOLD | NOT_MEASURED",
  "checks": [
    { "id": "POSITIVE_STEP", "expect": "ADVANCE", "got": "ADVANCE", "result": "PASS" },
    { "id": "NEGATIVE_PUBLISH", "expect": "REJECTED", "got": "REJECTED", "result": "PASS" }
  ],
  "real_state": { "changed": false, "method": "", "negative_control": "PASS | FAIL | NOT_RUN" },
  "cost": { "ci": { "kind": "ESTIMATE", "usd": 0.024, "basis": "4 min × $0.006 linux 2-core" },
            "provider": { "kind": "UNKNOWN" } },
  "artifacts": [{ "path": "screenshots/publish-rejected.png", "sha256": "" }]
}
```

규칙:
- `tested_sha`는 PR의 경우 merge commit(`GITHUB_SHA`)이다. `head_sha`는 `github.event.pull_request.head.sha`다.
- runner가 쓸 수 있는 `execution`은 `COMPLETED`와 `FAILED`뿐이다. **`TIMED_OUT`과 `OUTCOME_UNKNOWN`은 HQ가 도출한다.**
- `changed: false`는 `negative_control == PASS`일 때만 유효하다. 그렇지 않으면 `null` + `evaluation: NOT_MEASURED`.

**HQ 수용 규칙.** 모두 충족하면 ACCEPTED, 하나라도 빠지면 NOT_VERIFIED다.
1. GitHub API의 job 결론이 해당 run_id/attempt에서 success
2. `source.tested_sha`와 `run.id`가 API 기록과 일치
3. 필수 check가 모두 **존재**하고 PASS
4. `attempt == 1`, 또는 사람이 명시적으로 수용
5. HQ가 artifact를 다운로드해 sha256을 재계산하고 수집 기록에 남김
6. evidence가 없으면 NOT_MEASURED

## SAFE AUTOMATION BOUNDARY

| 자동 허용 | 자동 금지 |
|---|---|
| R1 테스트 실행 (PR / 수동) | State Promotion (Twin 단계 전진) |
| Evidence Packet 생성, artifact 업로드, Job Summary | 재시도 (Playwright retries, re-run, OUTCOME_UNKNOWN 재전송) |
| HQ가 GitHub API로 읽고 수용 규칙 판정 | Production 변경, 게시, 결제, Provider 호출, 자격증명 변경 |
| **Promotion Proposal** 작성 (`evaluation == PASS` + 수용 규칙 충족 시 "X→Y 제안"만) | runner → HQ push (webhook), 자동 merge, 자동 승인 |

**Promotion Proposal (Auto-Promotion 대체):** 제안은 자동으로 만들고, 적용은 사람이 한다. 적용은 DREAM CONTROL에서 사람이 클릭하거나, Twin 상태 파일을 바꾸는 PR을 사람이 merge하는 방식이다. 어느 쪽이든 플랜과 무관하게 동작하고 git에 기록이 남는다.

## FIRST IMPLEMENTABLE LOT

**LOT-1: 2번 Browser HOLD 해제 — R1만, secret 0개, 새 서비스 0개.**

**전제 (HQ):**
- 이 레인에 2번 저장소 접근 권한 부여
- GitHub 플랜 확인 (Free / Pro / Team)
- 2번 CI가 `pull_request`에서 fork 실행을 비활성 상태로 두고 있는지 확인

**2번 저장소의 비-main 브랜치에서 PR 1개:**
1. `.github/workflows/dream-verify.yml` — MINIMUM EXECUTION CONTRACT 규칙 1–8
2. Playwright 설정 — `retries: 0`, `trace: 'off'`, `webServer`로 2번의 **실제 UI** 기동
3. spec 1개 — POSITIVE_STEP, NEGATIVE_PUBLISH, 그리고 `real_state` negative control 1건(의도적 변경이 탐지되는지)
4. evidence 작성 스크립트 1개 — 약 40줄, MINIMUM EVIDENCE CONTRACT

**HQ 쪽:** 코드 없음. Job Summary와 artifact를 사람이 수용 규칙으로 판정한다. 이때 걸린 시간을 기록해 8.2(관리시간 절감) 실험값으로 쓴다.

**종료 조건:**
- 수용 규칙 6개 충족
- 월 예상 분량 = 실행 횟수 × 실측 분(ESTIMATE)으로 기록
- 실패 시 evidence 없음이 NOT_MEASURED로 표시되는지 1회 확인

**LOT-1에서 하지 않는 것:** AI Provider runner, R2, DREAM CONTROL 연동, 승격, 재시도.

## STOP

검토 결과만 반환한다. 구현, Production·Main 수정, Provider 호출, Browser 실행은 하지 않았다.
