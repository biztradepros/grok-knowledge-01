// Prints export/remote-kernel-v0.1-report.html to PDF with Chromium (A4, page numbers).
// usage: node export/render_pdf.js   (PLAYWRIGHT_MODULE=<path> if playwright is not installed locally)
import { dirname, join } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { statSync } from 'node:fs';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, 'remote-kernel-v0.1-report.html');
const out = join(here, 'remote-kernel-v0.1-report.pdf');

async function loadPlaywright() {
  try { return await import('playwright'); } catch {}
  if (process.env.PLAYWRIGHT_MODULE) return createRequire(import.meta.url)(process.env.PLAYWRIGHT_MODULE);
  throw new Error('playwright not found: npm i --no-save playwright, or set PLAYWRIGHT_MODULE');
}

const { chromium } = await loadPlaywright();
const browser = await chromium.launch();
const page = await browser.newPage();
await page.emulateMedia({ media: 'print', colorScheme: 'light' });
await page.goto(pathToFileURL(src).href);
await page.evaluate(() => document.fonts.ready);
await page.pdf({
  path: out,
  format: 'A4',
  printBackground: true,
  preferCSSPageSize: true,
  displayHeaderFooter: true,
  headerTemplate: '<span></span>',
  footerTemplate: `<div style="width:100%;font-size:8px;color:#777;padding:0 14mm;display:flex;justify-content:space-between;">
    <span>Remote Kernel v0.1 — HQ 반환 보고서</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`,
  outline: true,
  tagged: true,
});
await browser.close();
console.log(`export/remote-kernel-v0.1-report.pdf  ${(statSync(out).size / 1024).toFixed(0)} KiB`);
