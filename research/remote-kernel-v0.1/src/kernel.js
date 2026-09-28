import {
  PROTOCOL, KERNEL_VERSION, KERNEL_VERBS, STATUS, REASON, VERB_AUTHORITY, FORBIDDEN_KEYS,
  KERNEL_MAX_AUTHORITY, DEFAULT_TIMEOUT_MS, MAX_TIMEOUT_MS, DEFAULT_SESSION_TTL_MS,
  authorityRank, minAuthority,
} from './constants.js';
import { hashOf, plainCopy, findForbiddenKey } from './canonical.js';
import { sha256Hex } from './sha256.js';
import { validateCommand, commandHash, resultHash } from './envelope.js';
import { genesisTwin, applyDecision, createTwinStore, createLedger } from './twin-store.js';

/**
 * Site adapter contract. The adapter is the only code that knows what a stage means; it lives
 * in the site repository, next to the site engine, and is owned by the site.
 *
 * @typedef {object} SiteAdapter
 * @property {string} adapter_id
 * @property {string} adapter_version
 * @property {{site_id: string, site_name: string, factory_no: string}} identity
 * @property {{id: string, stages: string[], gates?: Record<string, {authority: string, human_gate?: boolean}>}} pipeline
 *           Linear stages. `gates[to]` sets the authority needed to enter `to` (default R1).
 * @property {Record<string, {authority: string, human_gate?: boolean, external_effect?: boolean, description?: string}>} [actions]
 *           Site verbs beyond the kernel four (e.g. PUBLISH). Declared so they can be refused precisely.
 * @property {string} [genesis_stage]   twin fork point, e.g. the real site's current stage (default stages[0])
 * @property {object} [genesis_facts]
 * @property {'R0'|'R1'} [max_authority]   the most this site grants a remote session (default R1)
 * @property {number} [max_timeout_ms]
 * @property {(ctx: StepContext) => Promise<import('./twin-store.js').StepDecision>} step
 * @property {(twin: object) => object} [project]  public view of the twin (default: whole twin)
 * @property {() => string|Promise<string>} realFingerprint  read-only hash of REAL site state
 *
 * @typedef {object} StepContext
 * @property {object} twin   deep-frozen twin; mutation throws
 * @property {string} from
 * @property {string} to     the only stage the kernel will accept for ADVANCE
 * @property {object} args
 * @property {{attempt: (kind: string) => never}} effects  every external effect is refused in v0.1
 */

const TIMEOUT_SIGNAL = Symbol('remote.timeout');

function withTimeout(promise, ms) {
  let timer;
  const timeout = new Promise((_, reject) => { timer = setTimeout(() => reject(TIMEOUT_SIGNAL), ms); });
  return Promise.race([promise, timeout]).finally(() => clearTimeout(timer));
}

const errorText = (e) => String(e?.message ?? e).slice(0, 200);
const safeId = (v) => (typeof v === 'string' && v.length <= 128 ? v : null);

export function createKernel({ adapter, clock = () => Date.now(), sessionTtlMs = DEFAULT_SESSION_TTL_MS }) {
  const { site_id: SITE_ID } = adapter.identity;
  const stages = adapter.pipeline.stages;
  const siteMax = minAuthority(adapter.max_authority ?? 'R1', KERNEL_MAX_AUTHORITY);
  const project = adapter.project ?? ((t) => t);
  const genesisStage = adapter.genesis_stage ?? stages[0];
  if (!stages.includes(genesisStage)) throw new Error(`genesis_stage ${genesisStage} is not a declared stage`);
  const store = createTwinStore(genesisTwin({
    site_id: SITE_ID, pipeline_id: adapter.pipeline.id, stage: genesisStage, facts: adapter.genesis_facts ?? {},
  }));
  const ledger = createLedger();
  const sessions = new Map();
  let sessionCounter = 0;

  const iso = (ms) => new Date(ms).toISOString();

  function finish(cmd, before, received, f, { decision = null, index = true } = {}) {
    const after = store.read();
    let data = f.data ?? {};
    let status = f.status;
    let reason = f.reason_code ?? null;
    const leak = findForbiddenKey({ data, hold: f.hold ?? null }, FORBIDDEN_KEYS);
    if (leak) { data = { blocked_path: leak }; status = STATUS.FAILED; reason = REASON.LEAK_BLOCKED; }
    const result = {
      kind: 'remote.result',
      protocol: PROTOCOL,
      kernel_version: KERNEL_VERSION,
      adapter: { id: adapter.adapter_id, version: adapter.adapter_version },
      site_id: SITE_ID,
      command_id: safeId(cmd?.command_id),
      idempotency_key: safeId(cmd?.idempotency_key),
      session_id: f.session_id ?? safeId(cmd?.session_id),
      verb: safeId(cmd?.verb),
      status,
      reason_code: reason,
      hold: f.hold ?? null,
      data,
      twin: {
        stage_before: before.stage, stage_after: after.stage,
        seq_before: before.seq, seq_after: after.seq,
        hash_before: hashOf(before), hash_after: hashOf(after),
      },
      real_state_changed: f.real_state_changed ?? false,
      real_state_probe: f.real_state_probe ?? 'NOT_REACHED',
      side_effect_count: 0,
      evidence_refs: decision?.evidence_refs ?? [],
      lineage: {
        command_hash: f.command_hash ?? null,
        issued_by: safeId(cmd?.issued_by),
        retry_of: safeId(cmd?.lineage?.retry_of),
        parent_result_hash: safeId(cmd?.lineage?.parent_result_hash),
        prev_result_hash: ledger.lastHash(),
      },
      timing: { received_at: iso(received), completed_at: iso(clock()) },
    };
    result.result_hash = resultHash(result);
    ledger.append(result, decision, { index });
    return plainCopy(result);
  }

  function requirementFor(verb) {
    if (VERB_AUTHORITY[verb]) return { authority: VERB_AUTHORITY[verb], human_gate: false, kind: 'kernel' };
    const action = adapter.actions?.[verb];
    return action ? { ...action, kind: 'action' } : null;
  }

  // Order matters: human gate first (no remote authority can satisfy it), then the kernel
  // ceiling (R2 is off in v0.1), then what this session was granted.
  function authorityRefusal(req, granted) {
    if (req.human_gate) return REASON.HUMAN_GATE_REQUIRED;
    if (authorityRank(req.authority) > authorityRank(KERNEL_MAX_AUTHORITY)) return REASON.R2_DISABLED;
    if (authorityRank(req.authority) > authorityRank(granted)) return REASON.AUTHORITY_INSUFFICIENT;
    return null;
  }

  function identify(cmd) {
    const requested = cmd.args?.requested_authority ?? 'R0';
    const granted = minAuthority(requested, siteMax);
    sessionCounter += 1;
    const session_id = 'ses.' + sha256Hex(`${SITE_ID}|${cmd.idempotency_key}|${sessionCounter}`).slice(0, 20);
    const expires = clock() + sessionTtlMs;
    sessions.set(session_id, { granted, expires, issued_by: cmd.issued_by });
    const twin = store.read();
    return {
      status: STATUS.OK,
      session_id,
      data: {
        identity: adapter.identity,
        protocol: PROTOCOL,
        kernel_version: KERNEL_VERSION,
        adapter: { id: adapter.adapter_id, version: adapter.adapter_version },
        capabilities: {
          verbs: [...KERNEL_VERBS],
          inspect_views: ['twin', 'hold'],
          pipeline: plainCopy(adapter.pipeline),
          actions: plainCopy(adapter.actions ?? {}),
          max_authority: siteMax,
        },
        session: {
          session_id, requested_authority: requested, granted_authority: granted, expires_at: iso(expires),
          ...(requested !== granted ? { note: authorityRank(requested) > authorityRank(KERNEL_MAX_AUTHORITY) ? REASON.R2_DISABLED : 'SITE_MAX_AUTHORITY' } : {}),
        },
        twin: { stage: twin.stage, seq: twin.seq, hash: hashOf(twin) },
      },
    };
  }

  function inspect(cmd) {
    const twin = store.read();
    const view = cmd.args?.view ?? 'twin';
    if (view === 'hold') {
      // EXPLAIN_HOLD: the reasons recorded when the STEP was held. Recorded, not recomputed,
      // so the explanation is exactly what the site decided at that seq.
      return {
        status: STATUS.OK,
        data: { view, stage: twin.stage, seq: twin.seq, on_hold: twin.hold !== null, hold: twin.hold },
      };
    }
    if (view !== 'twin') return { status: STATUS.REJECTED, reason_code: REASON.SCHEMA_INVALID, data: { detail: `unknown view ${view}` } };
    return { status: STATUS.OK, data: { view, twin_hash: hashOf(twin), public: project(twin) } };
  }

  function fetchResult(cmd) {
    const entry = ledger.findByCommandId(cmd.args?.command_id);
    if (!entry) return { status: STATUS.REJECTED, reason_code: REASON.NOT_FOUND, data: { command_id: cmd.args?.command_id ?? null } };
    return { status: STATUS.OK, data: { found: true, result: entry.result } };
  }

  async function step(cmd, session) {
    const twin = store.read();
    if (cmd.expect_seq !== twin.seq) {
      return { f: { status: STATUS.REJECTED, reason_code: REASON.STALE_TWIN, data: { expect_seq: cmd.expect_seq, seq: twin.seq } } };
    }
    const at = stages.indexOf(twin.stage);
    if (at === stages.length - 1) return { f: { status: STATUS.REJECTED, reason_code: REASON.TERMINAL_STAGE } };
    const to = stages[at + 1];
    const gate = { authority: 'R1', ...(adapter.pipeline.gates?.[to] ?? {}) };
    const refusal = authorityRefusal(gate, session.granted);
    if (refusal) {
      // Kernel-level lock: the adapter is never asked about a transition it may not make.
      return { f: { status: STATUS.REJECTED, reason_code: refusal, data: { from: twin.stage, to, required_authority: gate.authority, human_gate: !!gate.human_gate } } };
    }

    let attempts = 0;
    const effects = Object.freeze({
      attempt(kind) { attempts += 1; throw new Error(`${REASON.SIDE_EFFECT_ATTEMPTED}: ${kind} refused at ${session.granted}`); },
    });
    const probe = async () => String(await adapter.realFingerprint());
    const realBefore = await probe();
    const timeout = Math.min(cmd.timeout_ms ?? DEFAULT_TIMEOUT_MS, adapter.max_timeout_ms ?? MAX_TIMEOUT_MS);
    let decision;
    let failure = null;
    try {
      decision = await withTimeout(
        Promise.resolve().then(() => adapter.step({ twin, from: twin.stage, to, args: plainCopy(cmd.args ?? {}), effects })),
        timeout,
      );
    } catch (e) {
      failure = e === TIMEOUT_SIGNAL
        ? { status: STATUS.TIMEOUT, reason_code: REASON.ADAPTER_TIMEOUT, data: { timeout_ms: timeout } }
        : { status: STATUS.FAILED, reason_code: REASON.ADAPTER_ERROR, data: { error: errorText(e) } };
    }
    const realChanged = (await probe()) !== realBefore;
    const measured = { real_state_changed: realChanged, real_state_probe: 'MEASURED' };
    if (realChanged) return { f: { ...measured, status: STATUS.FAILED, reason_code: REASON.REAL_STATE_CHANGED } };
    if (attempts > 0) return { f: { ...measured, status: STATUS.FAILED, reason_code: REASON.SIDE_EFFECT_ATTEMPTED, data: { attempts } } };
    if (failure) return { f: { ...measured, ...failure } };

    const problem = checkDecision(decision, to);
    if (problem) return { f: { ...measured, status: STATUS.FAILED, reason_code: REASON.ILLEGAL_TRANSITION, data: { detail: problem } } };
    const next = applyDecision(twin, decision);
    const data = { decision: decision.decision, from: twin.stage, to: next.stage, public: project(next) };
    const leak = findForbiddenKey({ decision, data }, FORBIDDEN_KEYS);
    if (leak) return { f: { ...measured, status: STATUS.FAILED, reason_code: REASON.LEAK_BLOCKED, data: { blocked_path: leak } } };

    store.commit(twin.seq, next);
    return {
      f: { ...measured, status: decision.decision === 'ADVANCE' ? STATUS.OK : STATUS.HOLD, hold: next.hold, data },
      decision,
    };
  }

  async function dispatch(cmd, received) {
    const before = store.read();
    const errors = validateCommand(cmd);
    if (errors.length) {
      return finish(cmd, before, received, { status: STATUS.REJECTED, reason_code: REASON.SCHEMA_INVALID, data: { errors } }, { index: false });
    }
    const command_hash = commandHash(cmd);
    const reject = (reason_code, data = {}, index = true) =>
      finish(cmd, before, received, { status: STATUS.REJECTED, reason_code, data, command_hash }, { index });

    if (cmd.site_id !== SITE_ID) return reject(REASON.SITE_MISMATCH, { expected: SITE_ID }, false);

    let session = null;
    if (cmd.verb !== 'IDENTIFY') {
      session = sessions.get(cmd.session_id);
      if (!session) return reject(REASON.NO_SESSION, {}, false);
      if (clock() > session.expires) return reject(REASON.SESSION_EXPIRED, {}, false);
    }

    const prior = ledger.findByKey(SITE_ID, cmd.idempotency_key);
    if (prior) {
      if (prior.result.lineage.command_hash === command_hash) return { ...plainCopy(prior.result), replayed: true };
      return reject(REASON.IDEMPOTENCY_CONFLICT, { original_command_id: prior.result.command_id }, false);
    }

    const req = requirementFor(cmd.verb);
    if (!req) return reject(REASON.UNKNOWN_VERB, { verbs: [...KERNEL_VERBS] });
    const granted = session?.granted ?? 'R0';
    const refusal = authorityRefusal(req, granted);
    if (refusal) return reject(refusal, { verb: cmd.verb, required_authority: req.authority, human_gate: !!req.human_gate, granted });
    if (req.kind === 'action') return reject(REASON.ACTION_NOT_EXECUTABLE, { verb: cmd.verb });

    switch (cmd.verb) {
      case 'IDENTIFY': return finish(cmd, before, received, { ...identify(cmd), command_hash });
      case 'INSPECT': return finish(cmd, before, received, { ...inspect(cmd), command_hash });
      case 'RESULT': return finish(cmd, before, received, { ...fetchResult(cmd), command_hash });
      case 'STEP': {
        const { f, decision } = await step(cmd, session);
        return finish(cmd, before, received, { ...f, command_hash }, { decision });
      }
      default: return reject(REASON.UNKNOWN_VERB);
    }
  }

  return {
    site_id: SITE_ID,
    // Never throws: one site's failure is always a FAILED result packet, never an HQ crash.
    async handle(cmd) {
      const received = clock();
      try {
        return await dispatch(cmd, received);
      } catch (e) {
        return finish(cmd, store.read(), received, { status: STATUS.FAILED, reason_code: REASON.KERNEL_ERROR, data: { error: errorText(e) } }, { index: false });
      }
    },
    twin: () => store.read(),
    genesis: () => store.genesis(),
    ledger: () => ledger.entries(),
    exportEvidence: () => ({ site_id: SITE_ID, genesis: store.genesis(), twin: store.read(), twin_hash: store.hash(), ledger: ledger.export() }),
  };
}

function checkDecision(d, to) {
  if (!d || typeof d !== 'object') return 'adapter returned no decision';
  if (d.decision === 'ADVANCE') {
    if (d.to !== to) return `ADVANCE must target ${to}, got ${d.to}`;
    if (d.evidence_refs !== undefined && !(Array.isArray(d.evidence_refs) && d.evidence_refs.every((r) => typeof r === 'string'))) {
      return 'evidence_refs must be strings';
    }
    return null;
  }
  if (d.decision === 'HOLD') {
    if (!Array.isArray(d.reasons) || d.reasons.length === 0) return 'HOLD needs at least one reason';
    if (!d.reasons.every((r) => typeof r?.code === 'string' && typeof r?.detail === 'string')) return 'hold reason needs code and detail';
    return null;
  }
  return `unknown decision ${d.decision}`;
}
