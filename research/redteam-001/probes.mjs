// RED-TEAM-001 probes against research/remote-kernel-v0.1. Each probe tries to BREAK a claim.
// No network, no provider, no production. Run: node research/redteam-001/probes.mjs
import { createKernel } from '../remote-kernel-v0.1/src/kernel.js';
import { makeCommand, resultHash } from '../remote-kernel-v0.1/src/envelope.js';
import { verifyChain } from '../remote-kernel-v0.1/src/twin-store.js';
import { createRefinerySite, prepareRefineryAdvance } from '../remote-kernel-v0.1/adapters/refinery-07.fixture.js';

const out = [];
const probe = (id, claim, broken, detail) => out.push({ id, claim, verdict: broken ? 'CLAIM_BROKEN' : 'CLAIM_HELD', detail });

async function boot(adapter) {
  const k = createKernel({ adapter });
  const id = await k.handle(makeCommand({ site_id: adapter.identity.site_id, verb: 'IDENTIFY', args: { requested_authority: 'R1' } }));
  return { k, cmd: (verb, x = {}) => makeCommand({ site_id: adapter.identity.site_id, session_id: id.session_id, verb, ...x }) };
}

// P1: "at-most-once execution". Idempotency lives in memory: a site restart forgets it.
{
  const { engine, adapter } = createRefinerySite();
  prepareRefineryAdvance(engine, 'M0');
  const a = await boot(adapter);
  const c = a.cmd('STEP', { expect_seq: 0, idempotency_key: 'idem.p1.fixed' });
  const r1 = await a.k.handle(c);
  const b = await boot(adapter);                         // same site, process restarted
  const r2 = await b.k.handle({ ...c, session_id: (await b.k.handle(makeCommand({ site_id: c.site_id, verb: 'IDENTIFY', args: { requested_authority: 'R1' } }))).session_id });
  probe('P1', 'same envelope executes at most once', r2.status === 'OK' && !r2.replayed,
    `before restart: ${r1.status}; after restart same key: ${r2.status}, replayed=${!!r2.replayed}`);
}

// P2: "hash chain = tamper-evident lineage". Without an external anchor, a rewriter just re-chains.
{
  const { adapter } = createRefinerySite();
  const { k, cmd } = await boot(adapter);
  await k.handle(cmd('PUBLISH'));
  const forged = JSON.parse(JSON.stringify(k.ledger()));
  let prev = null;
  for (const e of forged) {
    if (e.result.verb === 'PUBLISH') { e.result.status = 'OK'; e.result.reason_code = null; }
    e.result.lineage.prev_result_hash = prev;
    e.result.result_hash = resultHash(e.result);
    prev = e.result.result_hash;
  }
  const v = verifyChain(forged);
  probe('P2', 'hash chain detects a rewritten ledger', v.ok, `forged "PUBLISH -> OK" ledger verifyChain.ok=${v.ok}`);
}

// P3: "real_state_changed is measured, not a constant". The site supplies the fingerprint;
// a constant fingerprint makes the probe report MEASURED + false while real state changes.
{
  const { engine, adapter } = createRefinerySite();
  prepareRefineryAdvance(engine, 'M0');
  const blind = { ...adapter, realFingerprint: () => 'constant', step: async (ctx) => { engine._corruptReal(); return adapter.step(ctx); } };
  const { k, cmd } = await boot(blind);
  const r = await k.handle(cmd('STEP', { expect_seq: 0 }));
  probe('P3', 'REAL_STATE_CHANGED=false means real state did not change', r.real_state_changed === false && engine.realSnapshot().production_stage !== 'M1',
    `status=${r.status} probe=${r.real_state_probe} real_state_changed=${r.real_state_changed} real.production_stage=${engine.realSnapshot().production_stage}`);
}

// P4: "forbidden-key guard stops prompt leakage". Denylist checks key NAMES, not values.
{
  const { engine, adapter } = createRefinerySite();
  prepareRefineryAdvance(engine, 'M0');
  const leaky = { ...adapter, step: async ({ to }) => ({ decision: 'ADVANCE', to, facts: { note: 'SYSTEM PROMPT: you are the refinery…', api: { Authorization: 'Bearer ghp_EXAMPLEEXAMPLE' } } }) };
  const { k, cmd } = await boot(leaky);
  const r = await k.handle(cmd('STEP', { expect_seq: 0 }));
  probe('P4', 'secrets/prompts cannot reach the result packet', /ghp_EXAMPLE|SYSTEM PROMPT/.test(JSON.stringify(r)), `status=${r.status}; packet contains token/prompt text: ${/ghp_EXAMPLE/.test(JSON.stringify(r))}`);
}

for (const o of out) console.log(`${o.id} ${o.verdict.padEnd(12)} ${o.claim}\n    ${o.detail}`);
