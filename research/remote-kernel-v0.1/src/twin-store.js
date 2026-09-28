import { hashOf, plainCopy, deepFreeze } from './canonical.js';
import { resultHash } from './envelope.js';

/**
 * Digital twin state. Site-neutral: the kernel knows stages and sequence numbers, never what
 * a stage means. Site meaning lives in `facts`, written only through adapter decisions.
 * @typedef {object} TwinState
 * @property {string} site_id
 * @property {string} pipeline_id
 * @property {string} stage
 * @property {number} seq               increments on every committed STEP (advance or hold)
 * @property {null|{stage: string, at_seq: number, reasons: HoldReason[]}} hold
 * @property {string[]} evidence_refs   site artifact hashes accepted into the twin
 * @property {Record<string, object>} facts  public, site-projected facts per stage
 *
 * @typedef {{code: string, detail: string, evidence_key?: string}} HoldReason
 * @typedef {{decision: 'ADVANCE', to: string, evidence_refs?: string[], facts?: object}
 *         | {decision: 'HOLD', reasons: HoldReason[]}} StepDecision   HOLD never changes stage or facts
 */

export function genesisTwin({ site_id, pipeline_id, stage, facts = {} }) {
  return { site_id, pipeline_id, stage, seq: 0, hold: null, evidence_refs: [], facts };
}

// Kernel-owned pure transition. Adapters propose decisions; only this function changes the twin,
// which is what makes replay deterministic even when the site engine is not (9 SKILL/AI).
export function applyDecision(twin, decision) {
  if (decision.decision === 'ADVANCE') {
    return {
      ...twin,
      stage: decision.to,
      seq: twin.seq + 1,
      hold: null,
      evidence_refs: [...twin.evidence_refs, ...(decision.evidence_refs ?? [])],
      facts: { ...twin.facts, [decision.to]: decision.facts ?? {} },
    };
  }
  return {
    ...twin,
    seq: twin.seq + 1,
    hold: { stage: twin.stage, at_seq: twin.seq + 1, reasons: decision.reasons },
  };
}

export function createTwinStore(genesis) {
  const frozenGenesis = deepFreeze(plainCopy(genesis));
  let state = frozenGenesis;
  return {
    genesis: () => frozenGenesis,
    read: () => state,
    hash: () => hashOf(state),
    // Compare-and-set on seq: a late (timed-out) adapter result can never land on a newer twin.
    commit(expectSeq, next) {
      if (state.seq !== expectSeq) throw new Error(`twin moved: expected seq ${expectSeq}, have ${state.seq}`);
      state = deepFreeze(plainCopy(next));
      return state;
    },
  };
}

// Append-only result log with a hash chain. Every result is recorded, rejections included:
// a refused PUBLISH is evidence too.
export function createLedger() {
  const entries = [];
  const byKey = new Map();
  const byCommandId = new Map();
  return {
    lastHash: () => (entries.length ? entries[entries.length - 1].result.result_hash : null),
    // index=false for rejections decided before the idempotency check (bad schema, no session):
    // they are logged, but must not burn the key, or a resend after reconnect could never run.
    append(result, decision = null, { index = true } = {}) {
      const entry = deepFreeze(plainCopy({ result, decision }));
      entries.push(entry);
      if (index && result.idempotency_key) byKey.set(`${result.site_id}|${result.idempotency_key}`, entry);
      if (index && result.command_id) byCommandId.set(result.command_id, entry);
      return entry;
    },
    findByKey: (siteId, key) => byKey.get(`${siteId}|${key}`) ?? null,
    findByCommandId: (commandId) => byCommandId.get(commandId) ?? null,
    entries: () => entries.slice(),
    export: () => plainCopy(entries),
  };
}

export function verifyChain(entries) {
  const errors = [];
  let prev = null;
  entries.forEach(({ result }, i) => {
    if (resultHash(result) !== result.result_hash) errors.push(`#${i} result_hash does not match content`);
    if (result.lineage.prev_result_hash !== prev) errors.push(`#${i} prev_result_hash breaks the chain`);
    prev = result.result_hash;
  });
  return { ok: errors.length === 0, errors, length: entries.length, head: prev };
}

// Rebuild the twin from genesis using only recorded decisions. Never calls a site engine.
export function replayTwin(genesis, entries) {
  const errors = [];
  let state = plainCopy(genesis);
  for (const { result, decision } of entries) {
    if (!decision) continue;
    if (hashOf(state) !== result.twin.hash_before) errors.push(`${result.command_id}: hash_before mismatch`);
    state = applyDecision(state, decision);
    if (hashOf(state) !== result.twin.hash_after) errors.push(`${result.command_id}: hash_after mismatch`);
  }
  return { ok: errors.length === 0, errors, state, hash: hashOf(state) };
}
