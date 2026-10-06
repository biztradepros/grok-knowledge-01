# apps/web — Next.js (App Router) component structure

```
app/
  (project)/[code]/
    layout.tsx                 # loads building + base scenario (server component)
    page.tsx                   # BUILDING VIEW (default)
    scenarios/page.tsx         # SCENARIO VIEW — compare N calc_runs side by side
    flow/page.tsx              # FLOW VIEW — dependency graph (React Flow + ELK/dagre layout)
    finance/page.tsx           # FINANCIAL VIEW — CAPEX / revenue / profit / BEP + tornado sensitivity
    evidence/page.tsx          # EVIDENCE VIEW — param table: value · status · confidence · evidence · approval
    ops/page.tsx               # OPERATIONS VIEW — HOLD / WAITING_HUMAN / NEXT ACTION (wf_run + approvals)
components/
  building/BuildingStack.tsx   # SVG stack, one <FloorSlot> per level; color = status (FIXED/ASSUMPTION/OPTION), badge = flags
  building/FloorPanel.tsx      # CLICK 1 → side panel: area, use, numbers, legal, evidence
  building/OptionPicker.tsx    # CLICK 2 → options for that slot, each with live preview delta
  graph/ImpactGraph.tsx        # highlights impact.impactedNodes path; edge label = delta
  finance/KpiStrip.tsx         # profit, rate, BEP, cost.total — every value links to lineage
  ai/CoachPanel.tsx            # streams ai_message; renders [[node_id]] from calc_run; shows verdict + coach_next
  ai/ApprovalCard.tsx          # human gate UI
lib/
  calc.ts                      # re-exports @dream/calc (same code as server → preview == persisted result)
  realtime.ts                  # Supabase channel subscription
  ai-render.ts                 # renderAiText + guard (never show unguarded AI numbers)
```

## CLICK 1 → CLICK 2 sequence

1. Click `3F` → `FloorPanel` shows live params + evidence (no network: already loaded).
2. Click `KM36` → **optimistic**: browser runs `@dream/calc` on the derived scenario (<10 ms), shows deltas tagged `PREVIEW`.
3. In parallel `POST /api/scenarios` + `POST /api/calc-runs` → server computes the same thing, persists, returns `inputHash`.
   If server hash ≠ client hash → show `ENGINE MISMATCH` (deploy skew) and trust the server.
4. If no BLOCK flag → `POST /api/ai-jobs` starts `scenario-review`; UI subscribes to `project:<code>`.
5. Realtime events stream reviewer messages into `CoachPanel`; `ApprovalCard` appears when the workflow reaches the human gate.

## Realtime pattern
- Use **Broadcast** for app events (small payloads, ids only) and refetch details via API — avoids the
  Postgres-changes payload cap and keeps RLS logic in one place.
- AI token streaming goes browser ← route handler (SSE) directly, not through the DB.
