# DAEHEUNG Computable Building — prototype skeleton (LOT-001)

> ⚠️ All numbers in `scenarios/` are **DUMMY placeholders**, not Daeheung data. They exist to prove the mechanics.

```
prototype/
├── packages/core/types.ts        # Parameter / Floor / MdOption / Scenario / CalcRun / ImpactReport
├── packages/calc/graph.ts        # generic DAG: topo sort, downstream impact, upstream lineage, edges for UI
├── packages/calc/model.ts        # Daeheung domain pack: formulas as code, ENGINE_VERSION
├── packages/calc/engine.ts       # resolve(scenario) → validate → evaluate → sha256 input hash; impact()
├── packages/calc/guard.ts        # AI number guard: [[node_id]] placeholders, rejects invented 억/원
├── packages/calc/engine.test.ts  # 10 tests (determinism, propagation, blocks, FIXED rules, guard)
├── packages/calc/demo.ts         # CLICK 1/2 demo: BASE-132 vs KM36-3F vs KM40-3F vs B3
├── scenarios/*.json              # model + 4 scenarios (selections + overrides only)
├── db/schema.sql                 # Postgres/Supabase schema; FIXED trigger; append-only versions
├── contracts/ai-job.schema.json  # vendor-neutral AI request/response
├── contracts/workflow.md         # durable scenario-review workflow with human gate
├── contracts/api.md              # REST + realtime events
└── apps/web/STRUCTURE.md         # Next.js views, CLICK 1→2 sequence, realtime pattern
```

Run (Node ≥ 22.6, no install needed):

```bash
npm run demo   # prints the four scenarios + impact path for 3F → KM36
npm test       # 10/10 pass
```

Verified in this session:
- `npm test` → 10 pass, 0 fail.
- `db/schema.sql` applied cleanly to PostgreSQL 16 (pgvector line stubbed); inserting a FIXED parameter without an
  APPROVED approval raised an error, and a scenario override with `"status":"FIXED"` violated the check constraint.
