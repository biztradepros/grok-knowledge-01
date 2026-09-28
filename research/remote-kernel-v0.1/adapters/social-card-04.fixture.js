import { hashOf } from '../src/canonical.js';

// 4 SOCIAL CARD — FIXTURE. SOURCE→RECIPE→ARTIFACT→QC→HANDOFF is a pure twin simulation (R1).
// PUBLISHED sits behind a human gate, declared twice on purpose:
//   * pipeline.gates.PUBLISHED  — so STEP at HANDOFF is refused by the kernel before the adapter runs;
//   * actions.PUBLISH           — so an explicit PUBLISH verb is refused with the same reason.
// Neither path has any code that could publish; the adapter has no publisher to call.

export const SOCIAL_STAGES = ['SOURCE', 'RECIPE', 'ARTIFACT', 'QC', 'HANDOFF', 'PUBLISHED'];

export function createSocialCardEngine() {
  const inputs = { source: null, recipe: null };
  const real = { published_posts: 0, scheduled_posts: 0 };

  function renderSpec() {
    // Local, deterministic "render": a card spec, not an uploaded asset.
    return { title: inputs.source.title.slice(0, 60), layout: inputs.recipe.layout, alt: inputs.source.alt ?? '' };
  }

  return {
    setSource(source) { inputs.source = source; },
    setRecipe(recipe) { inputs.recipe = recipe; },
    evaluate(to) {
      switch (to) {
        case 'RECIPE':
          return inputs.recipe ? { ok: true, facts: { layout: inputs.recipe.layout }, refs: [hashOf(inputs.recipe)] }
            : { ok: false, reasons: [{ code: 'MISSING_INPUT', evidence_key: 'recipe', detail: 'no recipe selected' }] };
        case 'ARTIFACT': {
          const spec = renderSpec();
          return { ok: true, facts: { artifact_ref: hashOf(spec) }, refs: [hashOf(spec)] };
        }
        case 'QC': {
          const spec = renderSpec();
          const fails = [];
          if (!spec.alt) fails.push({ code: 'QC_FAILED', evidence_key: 'alt_text', detail: 'card has no alt text' });
          if (spec.title.length < 5) fails.push({ code: 'QC_FAILED', evidence_key: 'title', detail: 'title too short' });
          return fails.length ? { ok: false, reasons: fails } : { ok: true, facts: { qc: 'pass' }, refs: [hashOf({ qc: spec })] };
        }
        case 'HANDOFF':
          return { ok: true, facts: { handoff: 'packet prepared, not delivered' }, refs: [hashOf({ handoff: renderSpec() })] };
        default:
          return { ok: false, reasons: [{ code: 'NO_SITE_RULE', detail: `no rule for ${to}` }] };
      }
    },
    hasSource: () => inputs.source !== null,
    realSnapshot: () => ({ ...real }),
  };
}

export function createSocialCardAdapter({ engine }) {
  return {
    adapter_id: 'f04.social-card.adapter',
    adapter_version: '0.1.0-fixture',
    identity: { site_id: 'F04.SOCIAL-CARD', site_name: 'SOCIAL CARD', factory_no: '4' },
    pipeline: {
      id: 'social.card-chain',
      stages: SOCIAL_STAGES,
      gates: { PUBLISHED: { authority: 'R2', human_gate: true } },
    },
    actions: {
      PUBLISH: { authority: 'R2', human_gate: true, external_effect: true, description: 'post the card to a social account' },
    },
    max_authority: 'R1',
    async step({ to }) {
      if (!engine.hasSource()) return { decision: 'HOLD', reasons: [{ code: 'MISSING_INPUT', evidence_key: 'source', detail: 'no source loaded' }] };
      const r = engine.evaluate(to);
      if (!r.ok) return { decision: 'HOLD', reasons: r.reasons };
      return { decision: 'ADVANCE', to, evidence_refs: r.refs, facts: r.facts };
    },
    realFingerprint: () => hashOf(engine.realSnapshot()),
  };
}

export function createSocialCardSite() {
  const engine = createSocialCardEngine();
  return { engine, adapter: createSocialCardAdapter({ engine }) };
}

// Conformance arrange-hook: the card studio loads a source and a recipe.
export function prepareSocialCardAdvance(engine) {
  engine.setSource({ title: 'Autumn launch card', alt: 'a red maple leaf on white' });
  engine.setRecipe({ layout: 'square-1080' });
}
