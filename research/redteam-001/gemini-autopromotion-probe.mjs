// Applies Gemini R&D-001 §4.2 "State Auto-Promotion" rule literally to three envelopes that
// its EvidenceContract allows. No network, no provider, no browser.
const autoPromote = (e) => e.executionStatus === 'SUCCESS' && e.sideEffects.realStateChanged === false;
const base = { runnerIdentity: 'gha-runner-ubuntu-latest-1', receiptTimestamp: '2026-09-28T00:00:00Z', evidenceArtifacts: [] };
const cases = [
  ['G1 refinery run ended in HOLD (missing source_manifest) — process exited normally',
    { ...base, executionStatus: 'SUCCESS', rawResult: { verdict: 'HOLD', reasons: ['MISSING_EVIDENCE: source_manifest'] }, sideEffects: { realStateChanged: false, costIncurredUsd: 0, externalCallsCount: 0 } }],
  ['G2 assertions failed but the wrapper script caught the error and exited 0',
    { ...base, executionStatus: 'SUCCESS', rawResult: { tests: { passed: 3, failed: 2 } }, sideEffects: { realStateChanged: false, costIncurredUsd: 0, externalCallsCount: 0 } }],
  ['G3 envelope written by a PR that edited the runner script (self-reported, nothing measured)',
    { ...base, executionStatus: 'SUCCESS', rawResult: 'ok', sideEffects: { realStateChanged: false, costIncurredUsd: 0, externalCallsCount: 0 } }],
];
for (const [name, env] of cases) console.log(`${autoPromote(env) ? 'PROMOTED    ' : 'not promoted'}  ${name}`);
