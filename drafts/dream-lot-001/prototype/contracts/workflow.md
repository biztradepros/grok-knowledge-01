# Workflow Contract v0 — `scenario-review` (durable, code-first)

Written against a generic durable-step API (`step.run`, `step.waitForEvent`, `step.sleep`).
Maps 1:1 onto Inngest, Trigger.dev, Vercel Workflow (WDK) or Temporal. Pick one; do not mix.

```ts
export const scenarioReview = workflow("scenario-review", async ({ event, step }) => {
  const { projectId, fromScenario, toScenario } = event.data;

  // 1. Deterministic first. Never ask an AI for a number.
  const run    = await step.run("calc",   () => calc.runAndPersist(toScenario));      // idempotent on input_hash
  const impact = await step.run("impact", () => calc.impact(fromScenario, toScenario));
  if (run.flags.some(f => f.severity === "BLOCK")) {
    await step.run("notify-block", () => notify.ops(projectId, run.flags));          // e.g. KM40 area shortfall
    return { status: "BLOCKED_BY_ENGINE", runId: run.id };                            // no AI spend on infeasible options
  }

  // 2. Fan out ONLY the roles the impact graph asked for (not every agent every time).
  const reviews = await Promise.all(impact.reviewRoles
    .filter(r => r !== "CHALLENGER")
    .map(role => step.run(`review:${role}`, () => ai.runJob({ role, run, impact }))));  // router picks the model

  // 3. Challenge only when it is worth it (see report §11 trigger rule).
  const needsChallenge = reviews.some(r => r.verdict !== "SUPPORT")
    || Math.abs(impact.deltas["profit"]?.after - impact.deltas["profit"]?.before) > policy.challengeThresholdKrw;
  const challenge = needsChallenge
    ? await step.run("challenge", () => ai.runJob({ role: "CHALLENGER", run, impact, thread: reviews, modelFamily: "different-from-reviewers" }))
    : null;

  // 4. Fact check every SOURCE/FACT finding against evidence chunks.
  const checked = await step.run("fact-check", () => ai.runJob({ role: "FACT_CHECKER", run, thread: [...reviews, challenge].filter(Boolean) }));

  // 5. HUMAN GATE. The workflow sleeps (days if needed) without holding a server.
  const approvalId = await step.run("request-approval", () => approvals.request("SCENARIO_REVIEW", toScenario, { run, reviews, challenge, checked }));
  const decision = await step.waitForEvent("approval.decided", { match: { approvalId }, timeout: "14d" });
  if (!decision || decision.state !== "APPROVED") return { status: "NOT_APPROVED", approvalId };

  // 6. Only now may proposed changes become parameter versions (still not FIXED unless separately approved).
  await step.run("apply-changes", () => params.applyApprovedChangeRequests(approvalId));
  await step.run("edge-dispatch", () => edge.send("scenario.reviewed", { projectId, toScenario, approvalId })); // Make/n8n: Slack, Drive, mail
  return { status: "APPROVED", runId: run.id };
});
```

Rules
- Every `step.run` is idempotent (keyed by job id / input_hash). Retries never double-write.
- Make/n8n never hold workflow state. They receive `edge.send(...)` events and call `/api/hooks/edge/*` back.
- `wf_run` row mirrors state for the OPERATIONS VIEW (`WAITING_HUMAN`, `waiting_for = approval:<id>`).
