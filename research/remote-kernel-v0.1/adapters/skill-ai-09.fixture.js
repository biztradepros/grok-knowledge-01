import { hashOf } from '../src/canonical.js';

// 9 SKILL/AI — FIXTURE. The point is the split between a non-deterministic producer and a
// deterministic twin:
//   * the site's AI jobs run on the site's own schedule (never triggered by a remote STEP:
//     that would be provider execution, which R1 forbids);
//   * each output is sealed as an artifact whose public face is {artifact_ref, eval};
//   * STEP only asks "is a sealed, passing artifact present for the next stage?".
// The twin records the ref, so replay never re-runs a model and prompts never leave the site.

export const SKILL_STAGES = ['SOURCE', 'RAW', 'KNOWLEDGE', 'REFINEMENT', 'CANDIDATE', 'EVIDENCE'];

export function createSkillAiEngine() {
  const internal = new Map();   // stage -> {prompt, model, output}   (never leaves the site)
  const sealed = new Map();     // stage -> {artifact_ref, eval}      (public face)
  const real = { knowledge_base_version: 3, provider_calls: 0 };

  return {
    // Site-side AI job. `output` may differ on every run; that is expected.
    produce(stage, { prompt, model, output, eval_passed = true, eval_band = 'B' }) {
      internal.set(stage, { prompt, model, output });
      sealed.set(stage, { artifact_ref: hashOf({ stage, output }), eval: { passed: eval_passed, band: eval_band } });
    },
    sealedArtifact: (stage) => sealed.get(stage) ?? null,
    realSnapshot: () => ({ ...real }),
    clearArtifacts() { internal.clear(); sealed.clear(); },
  };
}

export function createSkillAiAdapter({ engine }) {
  return {
    adapter_id: 'f09.skill-ai.adapter',
    adapter_version: '0.1.0-fixture',
    identity: { site_id: 'F09.SKILL-AI', site_name: 'SKILL / AI', factory_no: '9' },
    pipeline: { id: 'skill.knowledge-chain', stages: SKILL_STAGES },
    actions: {
      RUN_MODEL: { authority: 'R2', external_effect: true, description: 'provider execution (paid, non-deterministic)' },
    },
    max_authority: 'R1',
    async step({ to }) {
      const a = engine.sealedArtifact(to);
      if (!a) return { decision: 'HOLD', reasons: [{ code: 'ARTIFACT_NOT_READY', detail: `no sealed ${to} artifact yet` }] };
      if (!a.eval.passed) {
        return { decision: 'HOLD', reasons: [{ code: 'EVAL_FAILED', detail: `${to} artifact failed site evaluation (band ${a.eval.band})` }] };
      }
      return { decision: 'ADVANCE', to, evidence_refs: [a.artifact_ref], facts: { artifact_ref: a.artifact_ref, eval_band: a.eval.band } };
    },
    realFingerprint: () => hashOf(engine.realSnapshot()),
  };
}

export function createSkillAiSite() {
  const engine = createSkillAiEngine();
  return { engine, adapter: createSkillAiAdapter({ engine }) };
}

// Conformance arrange-hook: a site AI job ran (output deliberately non-deterministic).
export function prepareSkillAiAdvance(engine, to) {
  engine.produce(to, {
    prompt: `internal prompt for ${to}`,
    model: 'site-private-model',
    output: `${to} output ${Math.random().toString(36).slice(2)}`,
  });
}
