# API Contract v0 (Next.js route handlers / server actions)

All writes go through these. The browser may run `@dream/calc` locally for instant preview,
but only `POST /calc-runs` produces a persisted, citable number.

| Method | Path | Body | Returns | Who |
|---|---|---|---|---|
| GET  | `/api/projects/:code/building?version=` | – | floors, options, live params (+status, confidence, evidence count) | all |
| POST | `/api/scenarios` | `{code, modelVersionId, selections, overrides}` | scenario (rejects FIXED overrides) | editor |
| POST | `/api/calc-runs` | `{scenarioId}` | `CalcRun` (idempotent on engine_version+input_hash) | server only |
| GET  | `/api/impact?from=:scenarioA&to=:scenarioB` | – | `ImpactReport` (changed inputs, impacted nodes, deltas, review roles) | all |
| GET  | `/api/calc-nodes/:id/lineage?run=` | – | upstream inputs with status + evidence (EVIDENCE VIEW) | all |
| POST | `/api/ai-jobs` | `{role, task, scenarioId, calcRunId}` | job id; starts durable workflow `scenario-review` | editor / system |
| POST | `/api/change-requests` | `{key, proposedValue, proposedStatus, evidenceIds}` | CR + PENDING approval | editor / AI |
| POST | `/api/approvals/:id/decide` | `{state, reason}` | approval; emits `approval.decided` event to workflow engine | approver |
| POST | `/api/scenarios/:id/promote` | – | PENDING approval to make it BASE | editor |
| POST | `/api/hooks/edge/:source` | signed payload | 202 — inbound from Make/n8n (e.g. new quote PDF in Drive) | Make/n8n (HMAC) |

Events (Supabase Realtime broadcast channel `project:<code>`):
`calc_run.created {scenarioId, calcRunId, flags}` · `ai_job.state {jobId, state}` ·
`ai_message.created {jobId, role}` · `approval.pending {approvalId, subject}` · `wf_run.waiting {runId, waitingFor}`
