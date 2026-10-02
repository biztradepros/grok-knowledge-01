# DREAM AI 기억 레지스트리 (MEMORY_REGISTRY)

다른 AI가 이 파일 하나만 읽으면, 여러 AI(Claude·Grok·Gemini·GPT)가 남긴 자료가 어디 있는지 찾을 수 있다.

- 저장소: `biztradepros/grok-knowledge-01` (공개, 로그인 없이 읽기 가능)
- 기준일: 2026-10-02 · 작성: Claude
- 읽는 법: 아래 `raw` 주소를 그대로 열면 된다. 브랜치 이름이 주소에 들어 있다.
- 주의: main 이 아닌 브랜치의 글은 전부 **연구·제안(승인 전)** 이다. 사실이나 결정으로 인용하지 말 것.

RAW = `https://raw.githubusercontent.com/biztradepros/grok-knowledge-01`

## 1. Gemini 협업 기록

| 이름 | 내용 | 브랜치 / 경로 |
| --- | --- | --- |
| REDTEAM-001-GEMINI | Gemini 의 `Execution_and_Evidence_RD_Report.md` 를 Claude Code 가 독립 검증한 결과 (2026-09-28). CRITICAL C1–C10, 제안별 KEEP/SIMPLIFY/REJECT | `claude/remote-system-advanced-rd-5x2gsb` / `research/redteam-001/REDTEAM-001-GEMINI.md` |
| gemini-autopromotion-probe | Gemini 의 자동 승격 규칙을 깨는 실험 코드 (G1–G3) | 같은 브랜치 / `research/redteam-001/gemini-autopromotion-probe.mjs` |
| REDTEAM-001 | 직전 라운드 레드팀 (Gemini 원문 미수신 상태에서 작성) | 같은 브랜치 / `research/redteam-001/REDTEAM-001.md` |
| probes | P1–P6 실험 코드 | 같은 브랜치 / `research/redteam-001/probes.mjs` |
| remote-kernel-v0.1 REPORT | Minimum Remote Kernel v0.1 보고서 (대부분 REDTEAM-001 에서 REJECT, SUPERSEDED) | 같은 브랜치 / `research/remote-kernel-v0.1/REPORT.md` |
| CLAUDE-PRD-ULTRA-001 §10 | Claude 주장 A 와 Gemini 주장 B 가 충돌할 때의 처리 설계 (Verified-Contradiction Case) | `ccr-c712f9d8-4lzzun` / `research/CLAUDE-PRD-ULTRA-001.md` |

Gemini 원문 `Execution_and_Evidence_RD_Report.md` 자체는 **이 저장소에 없다.** 검증 문서에서 제목만 확인된다. Gemini 에게 원문을 이 저장소 `research/gemini/` 에 올려 달라고 하면 목록이 완성된다.

Gemini 제안에 나오는 이름 (존재 미확인): `verify-twin.yml`, `hq/dream-control/browser-harness/verify-browser.mjs`, `BROWSER-LOCAL-001`.

## 2. Claude 연구 기록

| 이름 | 내용 | 브랜치 / 경로 |
| --- | --- | --- |
| CLAUDE-PRD-001 | DREAM AGENTIC INTELLIGENCE — Minimum Kernel Research | `ccr-c712f9d8-4lzzun` / `research/CLAUDE-PRD-001.md` |
| CLAUDE-PRD-ULTRA-001 | The Minimum Autonomous Factory Problem | `ccr-c712f9d8-4lzzun` / `research/CLAUDE-PRD-ULTRA-001.md` |
| CL2-APPLIED-RD-001 | Justified Result Record v0.1 (accepted, HQ) | `ccr-c712f9d8-4lzzun` / `research/CL2-APPLIED-RD-001.md` |
| SOLVABLE-LOTS | 풀 수 있는 LOT 만들기 (다른 AI 인계 안내서) | `ccr-c712f9d8-4lzzun` / `research/SOLVABLE-LOTS.md` |
| JRR 스키마·검사기 | `jrr-v0.1.schema.json`, `jrr_check.py` | `ccr-c712f9d8-4lzzun` / `research/cl2/` |
| Claude Code Skill Scout v0.1 | Skill·MCP 탐색 프로그램 (소스 MCP 레지스트리: registry.modelcontextprotocol.io, npm registry) | `ccr-6842da12-ee5ncd` / `scout/README.md`, `scout/CLAUDE_CODE_SCOUT_HANDOFF.md`, `scout/scout.py` |
| 고칠 점 F1–F3 코드 | PR #2, 작업판 `AI_TASKS.md`, 소감 `devlog/2026-09-27-claude.md` | `claude/fix-f1-f3` |
| DRD-C-DATA-KNOW-002 | ROOM-07 × ROOM-12 경계 레드팀 (2026-09-28) | 저장소에 없음. 대표님께 파일로만 전달됨 |

## 3. 공개 페이퍼 (main, 승인됨)

| 이름 | 경로 |
| --- | --- |
| 접속 안내 | `main/llms.txt`, `main/CHAT.md`, `main/index.json` |
| 가상 인플루언서 전략 (Grok) | `main/rooms/grok-knowledge-01/virtual-influencer-strategy.md` |
| 있는 사례 위에 올리는 개발 계획 (Grok) | `main/rooms/grok-knowledge-01/dev-plan-2026.md` |

## 4. 더 이상 접근되지 않는 저장소

| 이름 | 상태 (2026-10-02 확인) |
| --- | --- |
| `biztradepros/dream-factory-control-center` (비공개, GPT 개발 저장소, 문서에서 "2번 저장소") | Not Found. 계정의 비공개 저장소 수가 0 으로 바뀜. 삭제 또는 이전된 것으로 보임 |
| 그 안에 있던 파일 (2026-09-25 목록) | `AI_HANDOFF.md`, `AI_CONNECTION_CANARY.md`, `MCP_ROUTER_V0_2.md`, `REVIEW_TASK_CLAUDE_GROK_M0_9.md`, `GROK_REVIEW_AIC_004.md`, `GPT_ENTERPRISE_PROCESSING_ARCHIVE.md`, `VERSION.md`, `DEVELOPMENT_CHART.md`, `REVIEW_PACK_CURRENT/`, `SKILLS/` |
| 관련 브랜치 (문서 언급) | `gpt/remote-slice-001-vr`, HEAD `81b96095…` |

## 5. 다른 AI 에게 보낼 한 줄

```
https://raw.githubusercontent.com/biztradepros/grok-knowledge-01/claude/memory-registry/MEMORY_REGISTRY.md 를 읽고, Gemini 협업 기록(1절) 파일들을 열어 핵심을 요약해 줘. main 이 아닌 브랜치 글은 승인 전 연구로만 취급해.
```
