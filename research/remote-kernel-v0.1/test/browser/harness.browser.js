// Real browser, real clicks, no public URL.
//   default target : file://<repo>/dist/remote-harness.html   (private repo never leaves the runner)
//   HARNESS_URL    : any other origin, e.g. a localhost static server or a bounded DREAM CONTROL route
// Writes evidence/ (summary.json, harness-evidence.json, screenshots) for upload as a CI artifact.
import { test, after, before } from 'node:test';
import assert from 'node:assert/strict';
import { mkdirSync, writeFileSync, existsSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';

const root = join(dirname(fileURLToPath(import.meta.url)), '..', '..');
const evidenceDir = join(root, 'evidence');
const target = process.env.HARNESS_URL ?? pathToFileURL(join(root, 'dist/remote-harness.html')).href;

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  if (process.env.PLAYWRIGHT_MODULE) return createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE);
  throw new Error('playwright not found: npm i --no-save playwright, or set PLAYWRIGHT_MODULE');
}

let browser, page;
const offOrigin = [];
const consoleErrors = [];
const verdicts = {};

before(async () => {
  if (!process.env.HARNESS_URL) assert.ok(existsSync(join(root, 'dist/remote-harness.html')), 'run npm run build:harness first');
  mkdirSync(evidenceDir, { recursive: true });
  const { chromium } = await loadPlaywright();
  browser = await chromium.launch(process.env.CHROMIUM_PATH ? { executablePath: process.env.CHROMIUM_PATH } : {});
  page = await browser.newPage({ viewport: { width: 1200, height: 900 } });
  const origin = new URL(target).origin;
  page.on('request', (r) => {
    const u = new URL(r.url());
    const sameOrigin = u.protocol === 'file:' ? target.startsWith('file:') : u.origin === origin;
    if (!sameOrigin && u.protocol !== 'data:') offOrigin.push(r.url());
  });
  page.on('console', (m) => { if (m.type() === 'error') consoleErrors.push(m.text()); });
  page.on('pageerror', (e) => consoleErrors.push(String(e)));
  await page.goto(target);
});

after(async () => {
  const evidence = page ? await page.evaluate(() => window.__harness.evidence()) : null;
  const summary = {
    target,
    browser: browser?.version() ?? null,
    commit: process.env.GITHUB_SHA ?? null,
    verdicts,
    off_origin_requests: offOrigin,
    console_errors: consoleErrors,
    note: 'Fixture sites (9/7/4 stand-ins). Proves the harness path and kernel contract, not the real factories.',
  };
  writeFileSync(join(evidenceDir, 'summary.json'), JSON.stringify(summary, null, 2));
  if (evidence) writeFileSync(join(evidenceDir, 'harness-evidence.json'), JSON.stringify(evidence, null, 2));
  await browser?.close();
});

const click = (id) => page.click(`#${id}`);
const status = () => page.getAttribute('#status', 'data-status');
const stage = () => page.getAttribute('#stage', 'data-stage');
const packet = async () => JSON.parse(await page.textContent('#packet'));
const selectSite = (key) => page.selectOption('#site', key);
const shot = (name) => page.screenshot({ path: join(evidenceDir, `${name}.png`), fullPage: true });

test('F07 refinery: STEP holds, EXPLAIN_HOLD names the missing evidence, site work unblocks it', async () => {
  await selectSite('F07');
  await click('btn-identify');
  assert.equal(await status(), 'OK');
  await click('btn-step');
  assert.equal(await status(), 'HOLD');
  assert.equal(await stage(), 'SOURCE');
  await click('btn-explain');
  const why = await packet();
  assert.equal(why.data.on_hold, true);
  assert.equal(why.data.hold.reasons[0].evidence_key, 'source_manifest');
  await shot('f07-hold-explained');
  await click('btn-site-work');
  await click('btn-step');
  assert.equal(await status(), 'OK');
  assert.equal(await stage(), 'M0');
  verdicts.F07_STEP_HOLD_THEN_ADVANCE = 'PASS';
});

test('F04 social card: twin reaches HANDOFF, PUBLISH ends COMMAND_REJECTED / HUMAN_GATE_REQUIRED', async () => {
  await selectSite('F04');
  await click('btn-identify');
  await click('btn-site-work');
  for (const to of ['RECIPE', 'ARTIFACT', 'QC', 'HANDOFF']) {
    await click('btn-step');
    assert.equal(await stage(), to);
  }
  const positive = await packet();
  assert.equal(positive.status, 'OK');
  verdicts.POSITIVE_STEP = 'PASS';

  await click('btn-step');
  const viaStep = await packet();
  await click('btn-publish');
  const viaVerb = await packet();
  for (const r of [viaStep, viaVerb]) {
    assert.equal(r.status, 'COMMAND_REJECTED');
    assert.equal(r.reason_code, 'HUMAN_GATE_REQUIRED');
    assert.equal(r.real_state_changed, false);
    assert.equal(r.side_effect_count, 0);
    assert.equal(r.twin.hash_before, r.twin.hash_after);
  }
  assert.equal(await stage(), 'HANDOFF');
  assert.equal(await page.getAttribute('#chain', 'data-ok'), 'true');
  await shot('f04-publish-rejected');
  verdicts.NEGATIVE_PUBLISH = 'PASS';
  verdicts.REAL_STATE_CHANGED = viaVerb.real_state_changed;
  verdicts.SIDE_EFFECT_COUNT = viaVerb.side_effect_count;
});

test('F09 skill/AI: STEP holds until a sealed artifact exists; no prompt ever reaches the page', async () => {
  await selectSite('F09');
  await click('btn-identify');
  await click('btn-step');
  assert.equal((await packet()).hold.reasons[0].code, 'ARTIFACT_NOT_READY');
  await click('btn-site-work');
  await click('btn-step');
  assert.equal(await stage(), 'RAW');
  const everything = JSON.stringify(await page.evaluate(() => window.__harness.evidence()));
  assert.doesNotMatch(everything, /internal prompt|site-private-model/);
  verdicts.F09_NO_PROMPT_LEAK = 'PASS';
});

test('conformance C01–C12 passes for all three fixture sites inside the browser', async () => {
  await click('btn-conformance');
  await page.waitForSelector('#conformance-summary[data-pass]:not([data-pass=""])');
  const pass = Number(await page.getAttribute('#conformance-summary', 'data-pass'));
  const fail = Number(await page.getAttribute('#conformance-summary', 'data-fail'));
  await shot('conformance');
  assert.equal(fail, 0);
  assert.equal(pass, 36);
  verdicts.CONFORMANCE = `${pass}/${pass + fail}`;
});

test('no off-origin request and no console error during the whole run', () => {
  assert.deepEqual(offOrigin, []);
  assert.deepEqual(consoleErrors, []);
  verdicts.NETWORK_ISOLATION = 'PASS';
});
