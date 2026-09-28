// Bundles the kernel, conformance suite, HQ client and site fixtures into ONE self-contained
// HTML file (dist/remote-harness.html). No server, no CDN, no network: it opens from file://,
// from a CI runner, or behind any authenticated route, so a private repo is never exposed.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execSync } from 'node:child_process';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const ORDER = [
  'src/constants.js', 'src/sha256.js', 'src/canonical.js', 'src/envelope.js', 'src/twin-store.js',
  'src/kernel.js', 'src/conformance.js', 'src/hq-client.js',
  'adapters/refinery-07.fixture.js', 'adapters/skill-ai-09.fixture.js', 'adapters/social-card-04.fixture.js',
  'adapters/index.js',
];
const EXPOSE = [
  'createKernel', 'createHqClient', 'runConformance', 'verifyChain', 'replayTwin', 'makeCommand',
  'SITE_FIXTURES', 'STATUS', 'REASON', 'PROTOCOL', 'KERNEL_VERSION',
];

const seen = new Map();
const parts = ORDER.map((rel) => {
  const src = readFileSync(join(root, rel), 'utf8')
    .replace(/^import\s[\s\S]*?\sfrom\s+['"][^'"]+['"];[ \t]*$/gm, '')
    .replace(/^export (?=(?:const|let|function|async function|class) )/gm, '');
  if (/^(?:import|export)\b/m.test(src)) throw new Error(`${rel}: unsupported import/export form`);
  for (const m of src.matchAll(/^(?:const|let|function|async function|class) ([A-Za-z_$][\w$]*)/gm)) {
    if (seen.has(m[1])) throw new Error(`top-level name clash: ${m[1]} in ${rel} and ${seen.get(m[1])}`);
    seen.set(m[1], rel);
  }
  return `// ---- ${rel} ----\n${src}`;
});
for (const name of EXPOSE) if (!seen.has(name)) throw new Error(`cannot expose missing ${name}`);

let commit = process.env.GITHUB_SHA ?? 'local';
try { if (commit === 'local') commit = execSync('git rev-parse HEAD', { cwd: root }).toString().trim(); } catch {}

const bundle = `(() => {\n'use strict';\n${parts.join('\n')}\nwindow.RemoteKernel = Object.freeze({ ${EXPOSE.join(', ')} });\n})();`;
const html = readFileSync(join(root, 'harness/harness.template.html'), 'utf8')
  .replace('/*__BUNDLE__*/', () => bundle)
  .replace('__BUILD_COMMIT__', commit)
  .replace('__BUILD_TIME__', new Date().toISOString());

mkdirSync(join(root, 'dist'), { recursive: true });
writeFileSync(join(root, 'dist/remote-harness.html'), html);
console.log(`dist/remote-harness.html  ${(html.length / 1024).toFixed(1)} KiB  commit=${commit.slice(0, 12)}`);
