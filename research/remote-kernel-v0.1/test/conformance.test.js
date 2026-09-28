import { test } from 'node:test';
import assert from 'node:assert/strict';
import { createKernel } from '../src/kernel.js';
import { runConformance } from '../src/conformance.js';
import { SITE_FIXTURES } from '../adapters/index.js';

for (const fx of SITE_FIXTURES) {
  test(`conformance ${fx.key}: C01..C12 all PASS on the reference kernel`, async () => {
    const checks = await runConformance({
      makeSite: fx.makeSite,
      prepareAdvance: fx.prepareAdvance,
      makeKernel: (adapter) => createKernel({ adapter }),
    });
    const failed = checks.filter((c) => c.status !== 'PASS');
    assert.deepEqual(failed, [], JSON.stringify(failed, null, 2));
    assert.equal(checks.length, 12);
  });
}
