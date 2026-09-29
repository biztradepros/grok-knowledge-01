---
id: CLAUDE-CL2-APPLIED-RD-001
title: FROM ULTRA THEORY TO SMALL WORKING RESULT — Justified Result Record v0.1
room: CL2 (CL1 에 전달하지 않음)
status: proposed
result: WORKS
date: 2026-09-29
---

# CL2-APPLIED-RD-001 — Justified Result Record v0.1

> 상태: proposed. 승인 페이퍼가 아니므로 `index.json` / `insights.json` 에 올리지 않는다.
> 실행물은 로컬 자가시험 하나뿐이다(표준 라이브러리, 네트워크 없음).

## 문제

결과가 **정확히 어떤 입력/증거를 소비했는지** 나중에 증명할 수 있게 기록하려면 무엇이 필요한가?
시험 장면은 하나다. P1 이 구현 A 를 만들고, 검증자 V 가 A 를 거절하고, P2 가 그 사실을 모른 채 A 를 소비해 테스트 결과 B 를 만든다.

## A. 스키마 — 주어진 8개 + 선택 필드 1개

파일: [`cl2/jrr-v0.1.schema.json`](cl2/jrr-v0.1.schema.json)

| 필드 | 뜻 |
|---|---|
| `task_id` | 작업 id |
| `result_id` | 기록마다 고유, 재사용 금지 |
| `produced_by` | 만든 주체 (v0.1 에서는 자기 선언, 인증 안 됨) |
| `consumes` | 이 결과가 바탕으로 삼은 결과들의 `result_hash` |
| `evidence_refs` | 로그·테스트 출력 등 증거 파일의 sha256 |
| `rule_version` | 판정 규칙 버전 (v0.1 규칙은 아직 읽지 않음) |
| `result_hash` | 결과 내용 바이트의 sha256 |
| `created_at` | 생성 시각 (판정에는 쓰지 않음) |
| **`rejects`** (선택) | 판정 기록에만 쓴다. 이 기록이 무효라고 선언하는 `result_hash` 목록 |

**`rejects` 를 더한 이유 (구체적 실패).** 주어진 8개 필드에는 "A 가 무효가 되었다"를 적을 자리가 없다.
`evidence_refs` 에 실패 로그를 넣을 수는 있지만, 그 기록이 *A 를* 무효로 만든다는 말은 어디에도 없다.
자가시험의 ablation 이 이를 보여 준다. `rejects` 를 지우면 B 는 `OK` 로 나온다 — 탐지 실패.

**쓰는 규칙 하나.** 판정 기록은 대상을 `consumes` 가 아니라 `rejects` 에 적는다.
대상을 `consumes` 에 넣으면 거절 기록 자신이 "무효인 A 를 소비했다"가 되어 STALE 로 잘못 판정된다.

`consumes` 가 id 가 아니라 **내용 해시**를 가리키므로 "정확히 어떤 입력인가"가 증명된다.
A 의 바이트를 가진 사람은 누구나 해시를 다시 계산해 B 가 소비한 입력과 대조할 수 있다.

## B. 예시 (실제 해시)

```json
[
  { "task_id": "T-001", "result_id": "R-A", "produced_by": "P1",
    "consumes": [], "evidence_refs": [], "rule_version": "jrr-0.1",
    "result_hash": "sha256:34073089d4c2b3c2ffa4f09dfcc8454d67c3e95980212b8a42948aef3a431c45",
    "created_at": "2026-09-29T10:00:00Z" },

  { "task_id": "T-001", "result_id": "R-V", "produced_by": "V",
    "consumes": [],
    "evidence_refs": ["sha256:1d80db1395dae5a788e09ddd8b71dccf08bfa271a0c1130386b408127454e4f5"],
    "rule_version": "jrr-0.1",
    "result_hash": "sha256:6b501ceab4c46cbe959f43175f8e254ae46c719c74b46c4fdce1739649ae578a",
    "created_at": "2026-09-29T10:05:00Z",
    "rejects": ["sha256:34073089d4c2b3c2ffa4f09dfcc8454d67c3e95980212b8a42948aef3a431c45"] },

  { "task_id": "T-001", "result_id": "R-B", "produced_by": "P2",
    "consumes": ["sha256:34073089d4c2b3c2ffa4f09dfcc8454d67c3e95980212b8a42948aef3a431c45"],
    "evidence_refs": ["sha256:d3b0cd1f6d438658b98e0b1d42965afb89e8767ead31f6b5ee327757d87a4560"],
    "rule_version": "jrr-0.1",
    "result_hash": "sha256:9c8bf18f90ee2b44fd280e7556a1a18be2ddf89b1bd520f03712713d030fe24d",
    "created_at": "2026-09-29T10:07:00Z" }
]
```

내용: A 는 `add()` 가 문자열을 돌려주는 구현이다(명세는 정수). V 의 타입 검사가 실패해 A 를 거절한다.
B 는 A 의 동작에 맞춰 쓴 테스트라서 A 위에서는 통과하지만, 버그를 그대로 굳힌다.

## C. 탐지 규칙

```
invalid(h)   ⇔  어떤 기록 v 가 h ∈ v.rejects

status(r) =
  INVALID           r.result_hash 가 invalid
  STALE_DEPENDENCY  r.consumes 의 어떤 h 가 invalid 이거나,
                    h 를 만든 기록의 status 가 STALE_DEPENDENCY
  UNRESOLVED        consumes 의 어떤 h 에 해당하는 기록이 없음 (정의만 함, 이번에 시험하지 않음)
  OK                그 밖
```

규칙은 시각을 읽지 않는다. 그래서 B 가 거절 전에 만들어졌든 후에 만들어졌든 같은 판정이 나온다.

## D. 자가시험

```
python3 research/cl2/jrr_check.py
```

출력 (요약):

```
R-A  INVALID           R-A rejected by R-V
R-V  OK
R-B  STALE_DEPENDENCY  R-B consumed R-A -> R-A rejected by R-V
8 fields only   -> R-B is OK (stale dependency not detectable)
8 + `rejects`   -> R-B is STALE_DEPENDENCY
PASS
```

## E. 결과: **WORKS**

기록만으로 `R-B → consumed R-A → R-A rejected by R-V` 사슬을 찾고 B 를 `STALE_DEPENDENCY` 로 판정한다.
조건: 주어진 8개 필드에 선택 필드 `rejects` 하나를 더해야 한다. 8개만으로는 **DOES_NOT_WORK** 이다.

## BACKLOG_CANDIDATE (최대 3)

1. **기록 무결성** — 저장된 기록을 나중에 고쳐도(예: B 의 `consumes` 한 글자) 지금은 알 수 없다.
2. **`produced_by` 인증** — 자기 선언이다. 누가 만들었는지는 증명되지 않는다 (ULTRA T2).
3. **`rule_version` 사용** — 기록만 되고 아직 어떤 판정에도 쓰이지 않는다. 규칙이 바뀐 뒤 옛 판정을 재현하는 방법이 없다.

## NEXT (하나)

**저장된 JRR 기록이 작성 후 수정되었는지 탐지할 수 있는가?**
자가시험 하나: B 의 `consumes` 를 한 글자 바꾸면 검사기가 FAIL 을 낸다.
