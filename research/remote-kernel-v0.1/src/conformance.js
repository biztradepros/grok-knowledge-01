import { STATUS, REASON, FORBIDDEN_KEYS } from './constants.js';
import { makeCommand } from './envelope.js';
import { findForbiddenKey } from './canonical.js';
import { verifyChain, replayTwin } from './twin-store.js';

/**
 * Site-neutral conformance checks. A site passes by supplying:
 *   makeSite()                 -> { adapter, engine }   fresh site, whose first STEP must HOLD
 *   prepareAdvance(engine, to) -> void                  site-side work so the next STEP can ADVANCE
 *   makeKernel(adapter)        -> kernel                (reference kernel, or a shim over an existing one)
 * The same list runs in node:test and in the browser harness.
 */
export async function runConformance({ makeSite, prepareAdvance, makeKernel }) {
  const checks = [];
  const check = async (id, title, fn) => {
    try {
      const detail = await fn();
      checks.push({ id, title, status: 'PASS', detail: detail ?? '' });
    } catch (e) {
      checks.push({ id, title, status: 'FAIL', detail: String(e?.message ?? e) });
    }
  };
  const assert = (cond, msg) => { if (!cond) throw new Error(msg); };

  const boot = async (authority = 'R1') => {
    const site = makeSite();
    const kernel = makeKernel(site.adapter);
    const site_id = site.adapter.identity.site_id;
    const id = await kernel.handle(makeCommand({ site_id, verb: 'IDENTIFY', args: { requested_authority: authority } }));
    const session_id = id.session_id;
    const cmd = (verb, extra = {}) => makeCommand({ site_id, session_id, verb, ...extra });
    return { site, kernel, site_id, id, session_id, cmd };
  };
  const untouched = (r) => r.twin.hash_before === r.twin.hash_after && r.real_state_changed === false && r.side_effect_count === 0;

  await check('C01', 'IDENTIFY: identity, capabilities, session; R2 request capped at R1', async () => {
    const { id } = await boot('R2');
    assert(id.status === STATUS.OK, `status ${id.status}`);
    assert(id.data.identity?.site_id && id.data.capabilities?.verbs?.length === 4, 'identity/capabilities missing');
    assert(id.data.session.granted_authority === 'R1', `granted ${id.data.session.granted_authority}`);
    return `granted=${id.data.session.granted_authority} note=${id.data.session.note}`;
  });

  await check('C02', 'R0 session cannot STEP (AUTHORITY_INSUFFICIENT, nothing changes)', async () => {
    const { kernel, cmd } = await boot('R0');
    const r = await kernel.handle(cmd('STEP', { expect_seq: 0 }));
    assert(r.status === STATUS.REJECTED && r.reason_code === REASON.AUTHORITY_INSUFFICIENT, `${r.status}/${r.reason_code}`);
    assert(untouched(r), 'twin or real state moved');
  });

  await check('C03', 'STEP without site evidence HOLDs; stage unchanged; EXPLAIN_HOLD returns the same reasons', async () => {
    const { kernel, cmd } = await boot();
    const before = kernel.twin().stage;
    const r = await kernel.handle(cmd('STEP', { expect_seq: 0 }));
    assert(r.status === STATUS.HOLD, `status ${r.status}`);
    assert(r.twin.stage_after === before, 'stage moved on HOLD');
    assert(r.hold?.reasons?.length > 0, 'no hold reasons');
    assert(r.real_state_probe === 'MEASURED' && r.real_state_changed === false, 'real state not measured/clean');
    const x = await kernel.handle(cmd('INSPECT', { args: { view: 'hold' } }));
    assert(x.status === STATUS.OK && x.data.on_hold, 'EXPLAIN_HOLD not on hold');
    assert(JSON.stringify(x.data.hold.reasons) === JSON.stringify(r.hold.reasons), 'explanation differs from recorded hold');
    return r.hold.reasons.map((h) => h.code).join(',');
  });

  await check('C04', 'STEP with site evidence ADVANCEs exactly one stage; real state measured unchanged; 0 side effects', async () => {
    const { site, kernel, cmd } = await boot();
    const stages = site.adapter.pipeline.stages;
    const from = kernel.twin().stage;
    const to = stages[stages.indexOf(from) + 1];
    prepareAdvance(site.engine, to);
    const r = await kernel.handle(cmd('STEP', { expect_seq: 0 }));
    assert(r.status === STATUS.OK, `status ${r.status}/${r.reason_code}`);
    assert(r.twin.stage_after === to && r.twin.seq_after === 1, `moved to ${r.twin.stage_after}`);
    assert(r.real_state_probe === 'MEASURED' && r.real_state_changed === false && r.side_effect_count === 0, 'isolation');
    return `${from}->${to}`;
  });

  await check('C05', 'Stale expect_seq is refused (STALE_TWIN)', async () => {
    const { kernel, cmd } = await boot();
    const r = await kernel.handle(cmd('STEP', { expect_seq: 7 }));
    assert(r.status === STATUS.REJECTED && r.reason_code === REASON.STALE_TWIN && untouched(r), `${r.status}/${r.reason_code}`);
  });

  await check('C06', 'Same envelope twice executes once (replayed, same result_hash)', async () => {
    const { site, kernel, cmd } = await boot();
    const stages = site.adapter.pipeline.stages;
    prepareAdvance(site.engine, stages[stages.indexOf(kernel.twin().stage) + 1]);
    const c = cmd('STEP', { expect_seq: 0 });
    const a = await kernel.handle(c);
    const b = await kernel.handle(c);
    assert(b.replayed === true && a.result_hash === b.result_hash, 'not replayed');
    assert(kernel.twin().seq === 1, `seq ${kernel.twin().seq}`);
  });

  await check('C07', 'Same key, different payload is refused (IDEMPOTENCY_CONFLICT)', async () => {
    const { kernel, cmd } = await boot();
    await kernel.handle(cmd('INSPECT', { idempotency_key: 'idem.fixed.1', args: { view: 'twin' } }));
    const r = await kernel.handle(cmd('INSPECT', { idempotency_key: 'idem.fixed.1', args: { view: 'hold' } }));
    assert(r.status === STATUS.REJECTED && r.reason_code === REASON.IDEMPOTENCY_CONFLICT, `${r.status}/${r.reason_code}`);
  });

  await check('C08', 'Unknown verbs and every declared external action are refused; nothing changes', async () => {
    const { site, kernel, cmd } = await boot();
    const u = await kernel.handle(cmd('DROP_TABLE'));
    assert(u.reason_code === REASON.UNKNOWN_VERB && untouched(u), 'unknown verb not refused');
    const out = [];
    for (const [verb, spec] of Object.entries(site.adapter.actions ?? {})) {
      const r = await kernel.handle(cmd(verb));
      const expected = spec.human_gate ? REASON.HUMAN_GATE_REQUIRED : REASON.R2_DISABLED;
      assert(r.status === STATUS.REJECTED && r.reason_code === expected && untouched(r), `${verb}: ${r.reason_code}`);
      out.push(`${verb}=${r.reason_code}`);
    }
    return out.join(',') || 'no declared actions';
  });

  await check('C09', 'Command for another site is refused (SITE_MISMATCH)', async () => {
    const { kernel, session_id } = await boot();
    const r = await kernel.handle(makeCommand({ site_id: 'F00.OTHER-SITE', session_id, verb: 'INSPECT' }));
    assert(r.reason_code === REASON.SITE_MISMATCH, r.reason_code);
  });

  await check('C10', 'Disconnect survival: resend after re-IDENTIFY replays, never re-executes', async () => {
    const { site, kernel, site_id, cmd } = await boot();
    const stages = site.adapter.pipeline.stages;
    prepareAdvance(site.engine, stages[stages.indexOf(kernel.twin().stage) + 1]);
    const c = cmd('STEP', { expect_seq: 0 });
    const first = await kernel.handle(c);             // HQ never sees this (link dropped)
    const again = await kernel.handle(makeCommand({ site_id, verb: 'IDENTIFY', args: { requested_authority: 'R1' } }));
    const resent = await kernel.handle({ ...c, session_id: again.session_id });
    assert(resent.replayed && resent.result_hash === first.result_hash && kernel.twin().seq === 1, 'resend re-executed');
    const fetched = await kernel.handle(makeCommand({ site_id, session_id: again.session_id, verb: 'RESULT', args: { command_id: c.command_id } }));
    assert(fetched.data.result.result_hash === first.result_hash, 'RESULT lookup mismatch');
  });

  await check('C11', 'Ledger hash chain verifies and replay rebuilds the twin without the site engine', async () => {
    const { site, kernel, cmd } = await boot();
    const stages = site.adapter.pipeline.stages;
    await kernel.handle(cmd('STEP', { expect_seq: 0 }));   // HOLD
    prepareAdvance(site.engine, stages[stages.indexOf(kernel.twin().stage) + 1]);
    await kernel.handle(cmd('STEP', { expect_seq: 1 }));   // ADVANCE
    await kernel.handle(cmd('PUBLISH'));                   // refusal is logged too
    const chain = verifyChain(kernel.ledger());
    assert(chain.ok, chain.errors.join('; '));
    const replay = replayTwin(kernel.genesis(), kernel.ledger());
    assert(replay.ok && replay.hash === kernel.exportEvidence().twin_hash, replay.errors.join('; ') || 'hash differs');
    return `${chain.length} entries`;
  });

  await check('C12', 'No result in the ledger carries a forbidden key (prompt/model/secret/...)', async () => {
    const { site, kernel, cmd } = await boot();
    const stages = site.adapter.pipeline.stages;
    prepareAdvance(site.engine, stages[stages.indexOf(kernel.twin().stage) + 1]);
    await kernel.handle(cmd('STEP', { expect_seq: 0 }));
    await kernel.handle(cmd('INSPECT'));
    const leak = findForbiddenKey(kernel.ledger().map((e) => e.result), FORBIDDEN_KEYS);
    assert(!leak, `leak at ${leak}`);
  });

  return checks;
}
