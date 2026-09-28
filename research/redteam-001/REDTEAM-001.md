# EXECUTION R&D RED-TEAM-001

2026-09-28 · Claude Code · 목표: 기능 추가가 아니라 제거. Production/Main/Provider 호출 없음.

## 0. 입력 상태

**첨부된 Gemini 연구결과는 수신되지 않았다.** 메시지 본문, `/mnt/attach`, 저장소 파일, 모든 브랜치, 이슈 4건과 PR 1건을 확인했으나 Gemini 원문은 없다. 원문의 항목별 판정은 **NOT_RUN**이다. 원문 내용을 추측해 판정하지 않았다.

이번에 공격한 대상은 원문 없이도 검증 가능한 두 가지다.
- (A) 직전 라운드에 Claude가 만든 `research/remote-kernel-v0.1/` 전체. 같은 질문("Execution Layer인가, 작은 계약인가")에 대한 가장 큰 기존 제안이다.
- (B) "Execution Layer" 범주 자체.

## 1. 결론

**DREAM에 지금 Execution Layer는 필요 없다.** 현재 모든 작업이 R1(실제 효과 금지)이므로 원격으로 "실행"할 대상이 없다. 스케줄, 큐, 워커, 타임아웃, 로그, 보관은 GitHub Actions가 이미 제공한다.

필요한 것은 두 가지뿐이다.
- **Runner Contract 1개:** 명령 하나, exit code, 증거 JSON 파일 하나
- **Evidence Schema 1개:** HQ가 GitHub 기록과 대조하는 판정 규칙 포함

v0.1 참조 커널(669줄)의 대부분은 **REJECT**다. 아래 공격 6건 중 6건이 v0.1의 핵심 주장을 깨뜨렸다.

## 2. 실행한 공격

재현 방법: `node research/redteam-001/probes.mjs` (P1–P4). P5와 P6은 scratch 사본에서 실행했다.

| ID | 공격한 주장 | 결과 | 증거 |
|---|---|---|---|
| P1 | "같은 envelope은 최대 1회 실행" | **CLAIM_BROKEN** | idempotency가 메모리에만 있다. Site 재시작 후 같은 키가 `OK, replayed=false`로 **다시 실행**된다 |
| P2 | "hash chain = 변조 탐지" | **CLAIM_BROKEN** | ledger의 `PUBLISH → REJECTED`를 `OK`로 고치고 체인을 다시 계산하면 `verifyChain.ok=true`. 외부 기준점이 없는 체인은 연출에 불과하다 |
| P3 | "`real_state_changed=false`는 측정값" | **CLAIM_BROKEN** | Site가 상수 fingerprint를 주면 실상태가 M1에서 M2로 바뀌어도 `probe=MEASURED, real_state_changed=false`. **증거를 PASS로 오인하게 되는 가장 위험한 경로** |
| P4 | "금지 키 guard가 prompt/secret 누출을 막는다" | **CLAIM_BROKEN** | 키 **이름**만 검사한다. `note: "SYSTEM PROMPT…"`, `api.Authorization: "Bearer ghp_…"` 가 `OK` 패킷으로 통과한다 |
| P5 | "browser summary.json = 신뢰할 증거" | **CLAIM_BROKEN** | human gate를 제거한 커널(PUBLISH 허용)로 실행: exit 1인데 `summary.json`에는 `PASS` 4개가 있고 overall `result` 필드가 없다. 실패 항목은 **목록에서 빠질 뿐** FAIL로 적히지 않는다. CI 템플릿은 이 파일을 `if: always()`로 업로드한다 |
| P6 | "evidence artifact에는 비밀이 없다" | **CLAIM_BROKEN** | Playwright trace(`trace.zip`)의 `trace.network`와 `trace.trace`에 `Authorization` 헤더와 세션 쿠키가 평문으로 저장된다. trace를 artifact로 올리면 저장소 읽기 권한자 전원에게 자격증명이 넘어간다 |

별도로, v0.1 브라우저 테스트 5/5 PASS는 **fixture 페이지**만 검증했다. 2번의 실제 UI 클릭 경로는 전혀 검증하지 않았다. 이 PASS를 2번 Browser HOLD 해제 근거로 쓰면 PASS 오인이 된다.

## 3. v0.1 구성요소 판정

| 구성요소 | 판정 | 이유 / 대체 |
|---|---|---|
| 4동사 원격 프로토콜 (IDENTIFY/INSPECT/STEP/RESULT) | **REJECT** | 실시간 원격 제어 수요가 아직 없다(REMOTE = OPTIONAL). HQ는 증거를 **읽기만** 하면 된다. 용어(ADVANCE/HOLD/REJECTED)만 남긴다 |
| Command/Result envelope (20여 필드) | **SIMPLIFY** | 10필드 Evidence Schema로 줄인다(§6) |
| Session·handshake·TTL | **REJECT** | CI 실행에는 세션이 없다. 인증되지 않은 bearer 문자열이라 오히려 위험 표면이다 |
| Capability discovery | **REJECT** | Factory 4개는 README 한 줄로 충분하다 |
| R0/R1/R2 권한 코드 | **REJECT (코드)** / KEEP (정책) | 강제는 구조로 한다: job에 secret 0개, `permissions: contents: read`. 자격증명이 없으면 R2는 **불가능**하다 |
| Human Gate | **KEEP (개념)** | 1순위: 게시 자격증명을 어떤 workflow에도 두지 않는다(무료, 가장 강함). 나중에 R2가 필요하면 GitHub Environments required reviewers(→ NEEDS_TEST) |
| Idempotency ledger | **REJECT** | P1: 거짓 보장. R1에서는 보호할 실제 효과가 없다. R2가 생기면 **대상 시스템의** idempotency key를 쓴다 |
| `expect_seq` 잠금, Twin Store, replay | **REJECT** | 공유되는 가변 twin이 없다. twin은 각 Factory 테스트 fixture이고, replay는 같은 SHA로 CI를 재실행하는 것이다 |
| Hash-chain ledger | **REJECT** | P2. 기준점은 GitHub의 run 기록(head_sha, conclusion, run_attempt)이다. HQ는 JSON이 아니라 GitHub API의 결론을 믿는다 |
| `real_state_probe` | **SIMPLIFY + NEEDS_TEST** | P3. **같은 실행 안에서 의도적 변경을 탐지한 negative control**이 PASS일 때만 `changed=false`를 인정한다 |
| 금지 키 leak guard | **REJECT (통제수단으로서)** | P4. 대체: job에 비밀을 두지 않고, trace를 끈다(P6) |
| Effects sink | **REJECT** | JS는 우회 가능하다. 구조적 통제(자격증명 0)가 대체한다 |
| Timeout | **KEEP** | `timeout-minutes` (기존 도구) |
| 자동 재시도 금지 | **KEEP** | Playwright `retries: 0`. `run_attempt > 1`은 PASS가 아니라 표시 대상 |
| Site 간 실패 격리 | **KEEP (무료)** | 저장소와 job이 이미 분리되어 있다 |
| 적합성 C01–C12 | **SIMPLIFY** | Factory별 필수 4개로 줄인다: POSITIVE, HOLD, NEGATIVE, NEGATIVE_CONTROL |
| 9/7/4 fixture 어댑터 | **REJECT (증거로서)** | 구조상 통과할 수밖에 없다. Factory 증거로 인용 금지 |
| HQ client, broadcast | **REJECT** | HQ는 GitHub API로 결론과 artifact를 읽는다 |
| 자체 SHA-256 | **REJECT** | `node:crypto`로 충분하다(standalone HTML을 버리면 필요 없음) |
| 자체 bundler + standalone harness HTML | **REJECT** | Playwright Test `webServer`로 **실제 앱**을 띄워 클릭한다 |
| 자체 브라우저 러너와 summary 작성기 | **REJECT** | P5. `@playwright/test`의 JSON reporter와 exit code를 쓴다 |
| CI 템플릿 | **SIMPLIFY (KEEP)** | trace off, retention 7, `result` 필드 필수, 증거 업로드는 하되 판정은 exit code로 |
| Factory별 커널 vendoring | **REJECT** | 사본 드리프트와 관리 업무 증가. 공유 대상은 schema 파일 하나뿐이다 |
| HTML/PDF 보고서 export와 폰트 서브셋 | **REJECT (앞으로)** | 저장소의 Markdown으로 충분하다 |

## 4. "Execution Layer" 범주 판정

| 흔한 구성요소 | 판정 | 기존 도구 |
|---|---|---|
| 작업 큐 / 스케줄러 | **REJECT** | Actions `on: pull_request / workflow_dispatch / schedule`, `concurrency` |
| 워커 풀 / 러너 관리 | **REJECT** | GitHub-hosted runner |
| 재시도 엔진 | **REJECT** | 재시도는 **금지** 대상이다. 필요한 것은 엔진이 아니라 `retries: 0` 설정이다 |
| 상태 DB / 실행 이력 | **REJECT** | Actions run 이력과 artifact |
| Provider SDK 래퍼 | **REJECT** | R2 금지 상태에서 호출할 대상이 없다. 만들면 자격증명 보관소가 생긴다 |
| 대시보드 | **REJECT** | Actions UI와 check 결과. HQ 요약은 나중에 GitHub API 스크립트 하나로 |
| 실행 권한·승인 계층 | **NEEDS_TEST** | R2 시점에 GitHub Environments. private repo 플랜 가용성 미확인 |

재검토 조건: R2 실행이 HQ 결정으로 허용되고, 같은 실제 효과가 2개 Factory 이상에서 반복될 때. 그 전에는 만들지 않는다.

## 5. 위험 항목별 판정

- **Credential leakage:**
  - P6의 trace가 최대 위험이다. `trace: 'off'`로 두고, 스크린샷은 인증 없는 R1 화면만 찍는다.
  - `persist-credentials: false`를 쓴다.
  - job에 `secrets.*` 참조를 0개로 둔다. lint로 강제한다(`grep -n 'secrets\.' dream-check.yml` 결과 0).
  - 이 연구물이 **public 저장소**에 있다는 점은 여전히 HQ 결정 사항이다(v0.1 D8).
- **Retry 위험:**
  - GitHub의 "Re-run failed jobs"는 코드 변경 없이 빨강을 초록으로 바꾼다. 그래서 `run_attempt`를 증거에 기록하고, attempt > 1은 자동 PASS가 아니다.
  - Playwright `retries > 0`은 한 번 실패한 테스트를 flaky로 표시하고 exit 0을 낸다(INFERRED, 문서화된 동작). 따라서 `retries: 0`.
- **Duplicate execution:**
  - R1에서는 실제 효과가 없으므로 중복 실행이 무해하다. 이 사실 자체가 v0.1의 idempotency 계층이 불필요한 이유다.
  - R2 도입 시 `concurrency` + `cancel-in-progress: false` + 대상 시스템의 idempotency key를 쓴다.
- **비용 폭증:**
  - 트리거를 PR `paths` 필터와 수동 실행으로 제한한다. 매 push나 cron에서 돌리지 않는다.
  - `timeout-minutes: 10`, retention 7일, trace off로 artifact 크기를 줄인다.
  - 추정(INFERRED): Factory 4곳 × 월 20회 × 4분 ≈ 월 320분. private repo 무료 분량과 가격은 NOT_VERIFIED이며, 현재 가격 페이지로 재확인해야 한다.
- **관리자 업무:**
  - v0.1은 Factory마다 커널 사본, 어댑터, 적합성 12개, harness, HQ client를 요구했다.
  - 최소안은 **파일 3개**다: workflow, check 스크립트, schema 사본.
- **Vendor lock-in:**
  - 계약이 "명령 + exit code + JSON"이라 Forgejo/Gitea Actions나 로컬 실행으로 옮길 수 있다.
  - 잠기는 부분은 선택 기능뿐이다(Environments, attestations). 필수로 만들지 않는다.
- **Evidence를 PASS로 오인:** P3, P5, fixture PASS, HQ-reported 2번 PASS. §6의 판정 규칙이 이 네 경로를 모두 막는다.

## 6. 가장 작은 실행 가능한 구조 (하나)

```
<factory-repo>/
  .github/workflows/dream-check.yml   ← 러너 (GitHub Actions)
  dream/check                         ← Factory 소유 명령. 자기 테스트만, R1만
  dream/evidence.schema.json          ← 공유 사본 1개
HQ: 새 코드 없음. GitHub에서 check 결론 + evidence.json 을 읽고 아래 규칙으로 판정
```

**Runner Contract v0 (규칙 5개)**
1. `dream/check`는 모든 check가 통과했을 때만 exit 0을 낸다. **판정의 진실은 exit code다.**
2. `evidence/evidence.json`을 schema에 맞게 쓴다. `result`는 exit 직전에 **마지막으로** 쓴다.
3. job에는 secret이 0개이고 `permissions: contents: read`다. 게시·결제·provider 자격증명이 없으므로 R2는 물리적으로 불가능하다.
4. `retries: 0`, trace off, `timeout-minutes: 10`.
5. 필수 check 4개:
   - `POSITIVE`: 조건 충족 시 ADVANCE
   - `HOLD`: 증거 부족 시 HOLD와 사유
   - `NEGATIVE`: R2 동작(PUBLISH 등)이 REJECTED
   - `NEGATIVE_CONTROL`: 실상태 변경 탐지기가 의도적 변경을 **실제로 잡는지**

**Evidence Schema v0 (10필드)**
```json
{
  "schema": "dream.evidence.v0",
  "factory": "F07",
  "commit": "<GITHUB_SHA>",
  "run": { "id": 0, "attempt": 1 },
  "mode": "R1",
  "result": "PASS | FAIL | NOT_RUN",
  "checks": [
    { "id": "HOLD", "expect": "HOLD", "got": "HOLD", "result": "PASS", "reasons": ["MISSING_EVIDENCE: source_manifest"] }
  ],
  "real_state": { "changed": false, "negative_control": "PASS" },
  "side_effects": { "count": 0, "negative_control": "PASS" },
  "artifacts": ["screenshots/hold.png"]
}
```

**HQ 판정 규칙.** 아래 여섯 가지를 모두 만족해야 PASS이고, 하나라도 빠지면 NOT_VERIFIED다.
1. **GitHub API의** check conclusion이 해당 SHA에서 `success`(JSON 자체 신고는 믿지 않는다)
2. `evidence.commit`이 그 SHA와 같다
3. `result == PASS`이고 필수 4개 check가 **모두 존재**하며 PASS다. 빠진 항목은 FAIL로 본다(P5 대응)
4. `run.attempt == 1`. 1이 아니면 사람이 명시적으로 수용해야 한다
5. `changed=false` / `count=0`은 해당 `negative_control == PASS`일 때만 인정한다(P3 대응)
6. fixture나 다른 저장소의 결과는 인용하지 않는다

**2번 Browser HOLD 적용:** 2번 저장소에 `dream-check.yml`을 넣고, Playwright Test `webServer`로 2번의 **실제 UI**를 띄워 STEP과 PUBLISH를 클릭한다. 커널, 프로토콜, harness HTML은 필요 없다. 2번에서 실행하기 전까지는 NOT_VERIFIED다.

## 7. NEEDS_TEST

| ID | 확인할 것 | 방법 |
|---|---|---|
| T1 | 2번 실제 UI를 Actions 안에서 `webServer`로 띄울 수 있는가 | 2번 저장소 접근 후 workflow 1회 실행 |
| T2 | 각 Factory의 실상태 변경 탐지기에 negative control을 만들 수 있는가 | Factory별로 의도적 변경 1건을 주입해 탐지되는지 확인 |
| T3 | private repo에서 Environments required reviewers를 쓸 수 있는 플랜인가 | R2 논의 시작 시 GitHub 설정 화면에서 확인 |
| T4 | Playwright `retries>0`이 flaky를 exit 0으로 보고하는가 | `@playwright/test`로 1회 실패 테스트를 넣어 exit code 확인 |
| T5 | private repo Actions 무료 분량과 artifact 한도 | 현재 GitHub 가격 페이지 |

## 8. Gemini 원문을 받으면

원문을 붙여 주면 원문의 제안 하나하나를 이 문서 §3과 같은 표 형식으로 KEEP / SIMPLIFY / REJECT / NEEDS_TEST 판정한다. 판정 기준은 §6의 최소 구조다. 그보다 무엇을 더 요구하는 제안은, 그것 없이는 §6이 실패함을 보여야 KEEP된다.

STOP.
