// AI number guard. AI prose may only reference engine numbers through
// placeholders like [[profit]] which the UI renders from the CalcRun.
// Any raw money figure typed by the model ("12.3억", "1,230,000,000원") must
// match an output of the cited run within tolerance, or the message is rejected.

import type { CalcRun } from "../core/types.ts";

export interface GuardResult {
  ok: boolean;
  unknownPlaceholders: string[];
  unmatchedNumbers: string[];
}

const PLACEHOLDER = /\[\[([a-zA-Z0-9_.]+)\]\]/g;
const EOK = /(-?\d[\d,]*(?:\.\d+)?)\s*억/g;      // 억 원
const WON = /(-?\d[\d,]{4,})\s*원/g;              // plain won, 5+ digits

export function guardAiText(text: string, run: CalcRun, toleranceEok = 0.05): GuardResult {
  const unknownPlaceholders = [...text.matchAll(PLACEHOLDER)].map((m) => m[1]).filter((id) => !(id in run.outputs));
  const money = Object.values(run.outputs).filter((v) => Math.abs(v) >= 1e6);
  const matches = (won: number) => money.some((v) => Math.abs(v - won) <= toleranceEok * 1e8);

  const unmatchedNumbers: string[] = [];
  for (const m of text.matchAll(EOK)) {
    if (!matches(Number(m[1].replace(/,/g, "")) * 1e8)) unmatchedNumbers.push(m[0]);
  }
  for (const m of text.matchAll(WON)) {
    if (!matches(Number(m[1].replace(/,/g, "")))) unmatchedNumbers.push(m[0]);
  }
  return { ok: unknownPlaceholders.length === 0 && unmatchedNumbers.length === 0, unknownPlaceholders, unmatchedNumbers };
}

/** Render placeholders for display: [[profit]] -> "76.4억" */
export function renderAiText(text: string, run: CalcRun): string {
  return text.replace(PLACEHOLDER, (_, id: string) => {
    const v = run.outputs[id];
    if (v === undefined) return `[[${id}?]]`;
    return Math.abs(v) >= 1e6 ? `${(v / 1e8).toFixed(1)}억` : String(v);
  });
}
