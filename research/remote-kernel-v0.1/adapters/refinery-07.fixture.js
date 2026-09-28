import { hashOf } from '../src/canonical.js';

// 7 DATA REFINERY — FIXTURE. The engine below is a stand-in for the real refinery; it holds no
// real M0/M1/M2 logic. What is real is the split: the adapter only translates the kernel's STEP
// into "ask the site's gate for stage X", and the kernel never learns how the gate decides.

export const REFINERY_STAGES = ['SOURCE', 'M0', 'M1', 'M2', 'M2_VERIFIED', 'F1_HANDOFF'];

// Site-owned policy. Stays inside the site; HQ only ever sees the resulting reason text.
const REQUIRED_EVIDENCE = {
  M0: ['source_manifest'],
  M1: ['m0_schema_report'],
  M2: ['m1_normalize_report'],
  M2_VERIFIED: ['m2_verify_report'],
  F1_HANDOFF: ['f1_handoff_packet'],
};
const VALUE_GATE = { min_value_score: 0.7, max_row_loss_ratio: 0.02 };

export function createRefineryEngine({ realStage = 'M1' } = {}) {
  const evidence = new Map();                       // site evidence store (site writes, adapter reads)
  const real = { production_stage: realStage, delivered_to_f1: false };

  return {
    // Site-side only: the refinery doing its own work. HQ has no path to this.
    recordEvidence(key, content) { evidence.set(key, { content, ref: hashOf({ key, content }) }); },
    // Read-only gate. Returns site meaning in site-neutral shape.
    gate(to) {
      const needed = REQUIRED_EVIDENCE[to] ?? [];
      const missing = needed.filter((k) => !evidence.has(k));
      let value_gate = null;
      if (to === 'M2_VERIFIED' && evidence.has('m2_verify_report')) {
        const { value_score, row_loss_ratio } = evidence.get('m2_verify_report').content;
        const fails = [];
        if (!(value_score >= VALUE_GATE.min_value_score)) fails.push(`value_score ${value_score} below site threshold`);
        if (!(row_loss_ratio <= VALUE_GATE.max_row_loss_ratio)) fails.push(`row_loss_ratio ${row_loss_ratio} above site threshold`);
        value_gate = { pass: fails.length === 0, reason: fails.join('; ') || 'value gate passed' };
      }
      const pass = missing.length === 0 && (value_gate?.pass ?? true);
      const present = needed.filter((k) => evidence.has(k));
      return {
        pass, missing, value_gate,
        evidence_refs: present.map((k) => evidence.get(k).ref),
        facts: { evidence_keys: present },
      };
    },
    realSnapshot: () => ({ ...real }),
    // Test hook for the isolation check: simulates a bug that writes real state.
    _corruptReal() { real.production_stage = 'M2'; },
  };
}

export function createRefineryAdapter({ engine, genesis_stage = 'SOURCE' }) {
  return {
    adapter_id: 'f07.refinery.adapter',
    adapter_version: '0.1.0-fixture',
    identity: { site_id: 'F07.DATA-REFINERY', site_name: 'DATA REFINERY', factory_no: '7' },
    pipeline: { id: 'refinery.m-chain', stages: REFINERY_STAGES },
    actions: {
      DELIVER_F1: { authority: 'R2', external_effect: true, description: 'real handoff of verified M2 to F1' },
    },
    genesis_stage,
    max_authority: 'R1',
    async step({ to }) {
      const g = engine.gate(to);
      if (!g.pass) {
        const reasons = g.missing.map((k) => ({ code: 'MISSING_EVIDENCE', evidence_key: k, detail: `${to} requires ${k}` }));
        if (g.value_gate && !g.value_gate.pass) reasons.push({ code: 'VALUE_GATE', detail: g.value_gate.reason });
        return { decision: 'HOLD', reasons };
      }
      return { decision: 'ADVANCE', to, evidence_refs: g.evidence_refs, facts: g.facts };
    },
    realFingerprint: () => hashOf(engine.realSnapshot()),
  };
}

export function createRefinerySite(opts = {}) {
  const engine = createRefineryEngine(opts);
  return { engine, adapter: createRefineryAdapter({ engine, ...opts }) };
}

// Conformance arrange-hook: the refinery doing its own work so that `to` can pass its gate.
const PASSING_EVIDENCE = {
  source_manifest: { files: 3, rows: 12000 },
  m0_schema_report: { schema_ok: true },
  m1_normalize_report: { normalized_rows: 11950 },
  m2_verify_report: { value_score: 0.82, row_loss_ratio: 0.004 },
  f1_handoff_packet: { format: 'f1.v1' },
};
export function prepareRefineryAdvance(engine, to) {
  for (const key of REQUIRED_EVIDENCE[to] ?? []) engine.recordEvidence(key, PASSING_EVIDENCE[key]);
}
