# ROOM-22 LIVE TEST CARDS — proposed by CLAUDE (LOT-002)

These cards turn the Runtime ARCHITECTURE_CONFLICT into measurements.
The kernel (`kernel/ledger.sql`) is the fixed reference. Make / n8n / code worker are the subjects under test.
Every result is stored as an EVIDENCE row of kind `LIVE_TEST`. Thresholds are pre-registered here, before the test runs.

| Card | What | How | PASS threshold (pre-registered) | Decides |
|---|---|---|---|---|
| **T1** Duplicate delivery | Same webhook to Make and to n8n, 20 times each, same idempotency key | Count `k_message` rows | exactly 1 per key, 0 duplicate side effects in the target SaaS | R2 holds for each adapter |
| **T2** Ledger write failure | Revoke the adapter's DB function permission mid-run, then restore it | Watch the outbox row + sweep | 100% of runs recovered by sweep, 0 lost, 0 double results | Make KEEP vs LIMIT |
| **T3** n8n Wait + fence | APPROVAL_REQUEST → n8n Wait (resume URL) → answer after the job version changed | Check that n8n passes `job_version_seen` | 100/100 stale resumes stored as STALE/LATE, 0 applied | n8n WAIT KEEP vs DB-wait only |
| **T4** Restart during wait | Restart / upgrade n8n while 10 executions wait 24–72 h | After restart, resume all 10 | 10/10 resume, or the kernel sweep escalates every lost one | n8n as WAIT owner-executor |
| **T5** Long AI research | 10–30 min research via the Make HTTP/AI module (sync) vs async callback | Measure timeouts against the 40-min scenario limit | async: 0 lost; sync: record failure rate | Make AI DISPATCH pattern |
| **T6** Side-by-side drain | Make and n8n both poll `k_claim` on the same event type for 1 h, 500 events | Count double claims / orphans | 0 double claims, 0 orphans older than claim timeout | Make+n8n = split-brain? |
| **T7** Trace completeness | 20 multi-AI jobs end-to-end | % of hops with `runtime_ref` + `job_id` round-tripped | ≥ 95% hops linked | Observability contract |
| **T8** Thread loss | Kill a provider thread mid-CHALLENGE (real Gemini/Claude/Grok) | `k_rehydrate` capsule → new thread | answer threads under the same parent in 5/5 cases, reviewer judges no context loss | SAME JOB recovery |
| **T9** Ops cost | Same 100 jobs through (a) Make only, (b) Make+n8n, (c) Make + kernel DB-wait | Make ops, n8n executions, operator minutes, incidents | report only (no threshold) → HQ cost decision | C vs A+kernel |
| **T10** Manual lane | A human pastes an external AI answer through the DREAM CONTROL paste form | Idempotency via content hash, artifact pointer | 0 duplicates, 100% stored with sender + parent | "zero copy-paste" path |

Order of execution: Shadow mode first (no behaviour change), then T1, T2, T6, T7 (1 week), then T3, T4, T8 (2 weeks, needs waiting time), then T5, T9, T10.

Verdict mapping: PASS → KEEP for that responsibility · partial → LIMIT (scope the responsibility down) · FAIL → REPLACE LATER or REJECT for that responsibility only. No test result removes a tool globally; each one decides one responsibility.
