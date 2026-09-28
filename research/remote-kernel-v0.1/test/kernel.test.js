import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { sha256Hex } from '../src/sha256.js';
import { canonicalJson, hashOf } from '../src/canonical.js';
import { createKernel } from '../src/kernel.js';
import { makeCommand } from '../src/envelope.js';
import { STATUS, REASON, AUTHORITY_LEVELS } from '../src/constants.js';
import { verifyChain, replayTwin } from '../src/twin-store.js';
import { createHqClient } from '../src/hq-client.js';
import { createRefinerySite, prepareRefineryAdvance, REFINERY_STAGES } from '../adapters/refinery-07.fixture.js';
import { createSkillAiSite, prepareSkillAiAdvance } from '../adapters/skill-ai-09.fixture.js';
import { createSocialCardSite, prepareSocialCardAdvance } from '../adapters/social-card-04.fixture.js';

const boot = async (adapter, opts = {}) => {
  const kernel = createKernel({ adapter, ...opts });
  const site_id = adapter.identity.site_id;
  const id = await kernel.handle(makeCommand({ site_id, verb: 'IDENTIFY', args: { requested_authority: 'R1' } }));
  const cmd = (verb, extra = {}) => makeCommand({ site_id, session_id: id.session_id, verb, ...extra });
  const step = () => kernel.handle(cmd('STEP', { expect_seq: kernel.twin().seq }));
  return { kernel, site_id, id, cmd, step };
};

test('sha256 matches node:crypto on vectors and unicode', () => {
  for (const s of ['', 'abc', 'a'.repeat(1000), '홀드 사유 — HOLD', '{"k":1}'.repeat(97)]) {
    assert.equal(sha256Hex(s), createHash('sha256').update(s, 'utf8').digest('hex'));
  }
});

test('canonical JSON is key-order independent and refuses NaN', () => {
  assert.equal(canonicalJson({ b: 1, a: [2, { d: 1, c: 2 }] }), canonicalJson({ a: [2, { c: 2, d: 1 }], b: 1 }));
  assert.throws(() => canonicalJson({ x: NaN }));
});

test('schema files agree with kernel constants', () => {
  const cmd = JSON.parse(readFileSync(new URL('../schema/command.v0.1.schema.json', import.meta.url)));
  const res = JSON.parse(readFileSync(new URL('../schema/result.v0.1.schema.json', import.meta.url)));
  assert.deepEqual(cmd.properties.args.properties.requested_authority.enum, AUTHORITY_LEVELS);
  assert.deepEqual([...res.properties.status.enum].sort(), Object.values(STATUS).sort());
  assert.deepEqual([...res.properties.reason_code.enum].filter(Boolean).sort(), Object.values(REASON).sort());
});

test('HQ client imports no site code (protocol-only coupling)', () => {
  const src = readFileSync(new URL('../src/hq-client.js', import.meta.url), 'utf8');
  assert.doesNotMatch(src, /from ['"]\.\.\/adapters|from ['"]\.\/kernel/);
});

// ---------- 7 DATA REFINERY ----------

test('F07: STEP != always advance — each stage HOLDs until the site records evidence', async () => {
  const { engine, adapter } = createRefinerySite();
  const { kernel, step, cmd } = await boot(adapter);
  for (let i = 1; i < REFINERY_STAGES.length; i++) {
    const to = REFINERY_STAGES[i];
    const held = await step();
    assert.equal(held.status, STATUS.HOLD, `${to} should hold first`);
    assert.equal(held.twin.stage_after, REFINERY_STAGES[i - 1]);
    const why = await kernel.handle(cmd('INSPECT', { args: { view: 'hold' } }));
    assert.ok(why.data.hold.reasons.some((r) => r.code === 'MISSING_EVIDENCE'));
    prepareRefineryAdvance(engine, to);
    const moved = await step();
    assert.equal(moved.status, STATUS.OK);
    assert.equal(moved.twin.stage_after, to);
  }
  assert.equal((await step()).reason_code, REASON.TERMINAL_STAGE);
  assert.ok(verifyChain(kernel.ledger()).ok);
});

test('F07: VALUE_GATE hold is explained with the site reason, not the site formula', async () => {
  const { engine, adapter } = createRefinerySite({ genesis_stage: 'M2' });
  const { kernel, step, cmd } = await boot(adapter);
  engine.recordEvidence('m2_verify_report', { value_score: 0.41, row_loss_ratio: 0.09 });
  const r = await step();
  assert.equal(r.status, STATUS.HOLD);
  const why = await kernel.handle(cmd('INSPECT', { args: { view: 'hold' } }));
  const gate = why.data.hold.reasons.find((x) => x.code === 'VALUE_GATE');
  assert.match(gate.detail, /value_score 0.41 below site threshold/);
  assert.match(gate.detail, /row_loss_ratio 0.09 above site threshold/);
  assert.doesNotMatch(JSON.stringify(why), /0\.7|0\.02/, 'site thresholds must not leave the site');
});

test('F07: real handoff (DELIVER_F1) is R2 and disabled in v0.1', async () => {
  const { adapter } = createRefinerySite();
  const { cmd, kernel } = await boot(adapter);
  const r = await kernel.handle(cmd('DELIVER_F1'));
  assert.equal(r.status, STATUS.REJECTED);
  assert.equal(r.reason_code, REASON.R2_DISABLED);
});

test('F07: an adapter that touches real state is caught by the probe and nothing commits', async () => {
  const { engine, adapter } = createRefinerySite();
  const rogue = { ...adapter, step: async (ctx) => { engine._corruptReal(); return adapter.step(ctx); } };
  prepareRefineryAdvance(engine, 'M0');
  const { kernel, step } = await boot(rogue);
  const r = await step();
  assert.equal(r.status, STATUS.FAILED);
  assert.equal(r.reason_code, REASON.REAL_STATE_CHANGED);
  assert.equal(r.real_state_changed, true, 'reported honestly, not hard-coded false');
  assert.equal(kernel.twin().seq, 0);
});

// ---------- 9 SKILL/AI ----------

test('F09: non-deterministic outputs, deterministic twin; replay needs no model', async () => {
  const { engine, adapter } = createSkillAiSite();
  const { kernel, step } = await boot(adapter);
  for (const to of ['RAW', 'KNOWLEDGE', 'REFINEMENT']) {
    assert.equal((await step()).status, STATUS.HOLD);
    prepareSkillAiAdvance(engine, to);
    assert.equal((await step()).status, STATUS.OK);
  }
  engine.clearArtifacts();                            // site data gone; replay must not care
  const replay = replayTwin(kernel.genesis(), kernel.ledger());
  assert.ok(replay.ok, replay.errors.join(';'));
  assert.equal(replay.hash, hashOf(kernel.twin()));
  const everything = JSON.stringify(kernel.exportEvidence());
  assert.doesNotMatch(everything, /internal prompt|site-private-model/);
});

test('F09: eval failure HOLDs with EVAL_FAILED; RUN_MODEL is R2 and disabled', async () => {
  const { engine, adapter } = createSkillAiSite();
  const { kernel, step, cmd } = await boot(adapter);
  engine.produce('RAW', { prompt: 'p', model: 'm', output: 'o', eval_passed: false, eval_band: 'D' });
  const r = await step();
  assert.equal(r.status, STATUS.HOLD);
  assert.equal(r.hold.reasons[0].code, 'EVAL_FAILED');
  assert.equal((await kernel.handle(cmd('RUN_MODEL'))).reason_code, REASON.R2_DISABLED);
});

test('F09: an adapter that leaks a prompt is blocked before commit', async () => {
  const { engine, adapter } = createSkillAiSite();
  const leaky = { ...adapter, step: async ({ to }) => ({ decision: 'ADVANCE', to, facts: { prompt: 'secret sauce' } }) };
  prepareSkillAiAdvance(engine, 'RAW');
  const { kernel, step } = await boot(leaky);
  const r = await step();
  assert.equal(r.reason_code, REASON.LEAK_BLOCKED);
  assert.equal(kernel.twin().stage, 'SOURCE');
  assert.doesNotMatch(JSON.stringify(r), /secret sauce/);
});

// ---------- 4 SOCIAL CARD ----------

test('F04: twin reaches HANDOFF; STEP to PUBLISHED and PUBLISH verb both end HUMAN_GATE_REQUIRED', async () => {
  const { engine, adapter } = createSocialCardSite();
  const { kernel, step, cmd } = await boot(adapter);
  const realBefore = JSON.stringify(engine.realSnapshot());
  prepareSocialCardAdvance(engine);
  for (const to of ['RECIPE', 'ARTIFACT', 'QC', 'HANDOFF']) assert.equal((await step()).twin.stage_after, to);

  const viaStep = await step();
  const viaVerb = await kernel.handle(cmd('PUBLISH', { args: { channel: 'instagram' } }));
  for (const r of [viaStep, viaVerb]) {
    assert.equal(r.status, 'COMMAND_REJECTED');
    assert.equal(r.reason_code, 'HUMAN_GATE_REQUIRED');
    assert.equal(r.real_state_changed, false);
    assert.equal(r.side_effect_count, 0);
    assert.equal(r.twin.hash_before, r.twin.hash_after);
  }
  assert.equal(viaStep.real_state_probe, 'NOT_REACHED', 'adapter must not even be asked');
  assert.equal(kernel.twin().stage, 'HANDOFF');
  assert.equal(JSON.stringify(engine.realSnapshot()), realBefore);
});

test('F04: QC without alt text HOLDs with QC_FAILED', async () => {
  const { engine, adapter } = createSocialCardSite();
  const { step } = await boot(adapter);
  engine.setSource({ title: 'Autumn launch card' });
  engine.setRecipe({ layout: 'square-1080' });
  await step(); await step();
  const r = await step();
  assert.equal(r.status, STATUS.HOLD);
  assert.deepEqual(r.hold.reasons.map((x) => x.evidence_key), ['alt_text']);
});

// ---------- failure modes ----------

const baseSite = () => createRefinerySite();

test('timeout: TIMEOUT result, late answer never commits, same key replays TIMEOUT, reissue carries retry_of', async () => {
  const { engine, adapter } = baseSite();
  prepareRefineryAdvance(engine, 'M0');
  let release;
  const slow = { ...adapter, step: (ctx) => new Promise((res) => { release = () => res(adapter.step(ctx)); }) };
  const { kernel, cmd, site_id, id } = await boot(slow);
  const c = cmd('STEP', { expect_seq: 0, timeout_ms: 30 });
  const r = await kernel.handle(c);
  assert.equal(r.status, STATUS.TIMEOUT);
  release();
  await new Promise((res) => setTimeout(res, 10));
  assert.equal(kernel.twin().seq, 0, 'late adapter answer must not land');
  const again = await kernel.handle(c);
  assert.equal(again.replayed, true);
  assert.equal(again.status, STATUS.TIMEOUT, 'kernel never retries on its own');

  const fast = createKernel({ adapter });  // separate kernel: explicit reissue path through HQ
  const hq = createHqClient({ transports: { [site_id]: (x) => fast.handle(x) } });
  await hq.identify(site_id);
  const first = await hq.step(site_id);
  const reissued = await hq.reissue(first.command_id);
  assert.equal(reissued.lineage.retry_of, first.command_id);
  assert.ok(id.session_id);
});

test('adapter throw -> FAILED; attempted side effect -> FAILED with side_effect_count 0; frozen twin', async () => {
  const { adapter } = baseSite();
  const throwing = { ...adapter, step: async () => { throw new Error('engine offline'); } };
  const effecting = { ...adapter, step: async (ctx) => { try { ctx.effects.attempt('http.post'); } catch {} return { decision: 'HOLD', reasons: [{ code: 'X', detail: 'x' }] }; } };
  const mutating = { ...adapter, step: async (ctx) => { ctx.twin.stage = 'F1_HANDOFF'; return null; } };

  const a = await (await boot(throwing)).step();
  assert.equal(a.reason_code, REASON.ADAPTER_ERROR);
  const b = await (await boot(effecting)).step();
  assert.equal(b.reason_code, REASON.SIDE_EFFECT_ATTEMPTED, 'swallowing the refusal does not hide it');
  assert.equal(b.side_effect_count, 0);
  const c = await (await boot(mutating)).step();
  assert.equal(c.reason_code, REASON.ADAPTER_ERROR);
  for (const r of [a, b, c]) assert.equal(r.twin.hash_before, r.twin.hash_after);
});

test('session expiry and no-session commands are refused without burning the idempotency key', async () => {
  let now = 1_000_000;
  const { adapter } = baseSite();
  const { kernel, cmd, site_id } = await boot(adapter, { clock: () => now, sessionTtlMs: 1000 });
  const c = cmd('INSPECT');
  now += 5000;
  assert.equal((await kernel.handle(c)).reason_code, REASON.SESSION_EXPIRED);
  const fresh = await kernel.handle(makeCommand({ site_id, verb: 'IDENTIFY', args: { requested_authority: 'R0' } }));
  const ok = await kernel.handle({ ...c, session_id: fresh.session_id });
  assert.equal(ok.status, STATUS.OK, 'same key still usable after reconnect');

  const orphan = makeCommand({ site_id, session_id: 'ses.unknown-to-site', verb: 'INSPECT' });
  assert.equal((await kernel.handle(orphan)).reason_code, REASON.NO_SESSION);
  const adopted = await kernel.handle({ ...orphan, session_id: fresh.session_id });
  assert.equal(adopted.status, STATUS.OK, 'NO_SESSION must not burn the key either');
});

test('HQ fan-out isolates failures: dead link, hung site and healthy site', async () => {
  const good = createRefinerySite();
  const hung = createSkillAiSite();
  const hungAdapter = { ...hung.adapter, step: () => new Promise(() => {}) };
  const kGood = createKernel({ adapter: good.adapter });
  const kHung = createKernel({ adapter: hungAdapter });
  const hq = createHqClient({
    transports: {
      'F07.DATA-REFINERY': (c) => kGood.handle(c),
      'F09.SKILL-AI': (c) => kHung.handle(c),
      'F04.SOCIAL-CARD': async () => { throw new Error('link down'); },
    },
  });
  const ids = ['F07.DATA-REFINERY', 'F09.SKILL-AI', 'F04.SOCIAL-CARD'];
  await hq.broadcast(ids, (s) => hq.identify(s));
  const out = await hq.broadcast(ids, (s) => hq.step(s, { timeout_ms: 40 }));
  assert.equal(out['F07.DATA-REFINERY'].status, STATUS.HOLD);
  assert.equal(out['F09.SKILL-AI'].status, STATUS.TIMEOUT);
  assert.equal(out['F04.SOCIAL-CARD'].status, 'DELIVERY_UNKNOWN');
});

test('HQ disconnect after delivery: redeliver replays, the site executed exactly once', async () => {
  const { engine, adapter } = baseSite();
  prepareRefineryAdvance(engine, 'M0');
  const kernel = createKernel({ adapter });
  let drop = false;
  const hq = createHqClient({
    transports: {
      'F07.DATA-REFINERY': async (c) => {
        const r = await kernel.handle(c);           // site always completes...
        if (drop) throw new Error('socket closed');   // ...HQ just never hears back
        return r;
      },
    },
  });
  await hq.identify('F07.DATA-REFINERY');
  drop = true;
  const lost = await hq.step('F07.DATA-REFINERY');
  assert.equal(lost.status, 'DELIVERY_UNKNOWN');
  drop = false;
  hq.forget('F07.DATA-REFINERY');
  await hq.identify('F07.DATA-REFINERY');
  const r = await hq.redeliver(lost.command_id);
  assert.equal(r.replayed, true);
  assert.equal(r.status, STATUS.OK);
  assert.equal(kernel.twin().seq, 1);
});
