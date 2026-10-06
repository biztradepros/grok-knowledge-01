// Deterministic engine: resolve(scenario) -> validate -> evaluate -> hash.
// Same resolved inputs + same ENGINE_VERSION => byte-identical CalcRun.
// The AI layer can only READ CalcRuns and PROPOSE parameter changes; it never
// calls evaluate() with its own numbers and never writes outputs.

import { createHash } from "node:crypto";
import type { AiRole, BuildingModel, CalcFlag, CalcRun, ImpactReport, Parameter, Scenario } from "../core/types.ts";
import { ENGINE_VERSION, SLOT_KEYS, buildGraph, podiumLevels } from "./model.ts";

export interface Resolved {
  params: Record<string, Parameter>; // every leaf input with its provenance
  numbers: Record<string, number>;
  flags: CalcFlag[];
}

export function resolve(model: BuildingModel, scenario: Scenario): Resolved {
  if (scenario.baseVersion !== model.baseVersion) {
    throw new Error(`scenario ${scenario.id} targets ${scenario.baseVersion}, model is ${model.baseVersion}`);
  }
  const params: Record<string, Parameter> = { ...model.params };
  const flags: CalcFlag[] = [];

  for (const floor of model.floors) {
    params[`floor.${floor.level}.area`] = floor.grossAreaM2;
    const use = scenario.selections[floor.level] ?? floor.currentUse;
    if (!floor.options.includes(use)) throw new Error(`${use} is not an allowed option for ${floor.level}`);
    const opt = model.optionCatalog[use];
    if (!opt) throw new Error(`unknown option ${use}`);
    for (const k of SLOT_KEYS) {
      const p = opt.params[k];
      if (!p) throw new Error(`option ${use} missing ${k}`);
      params[`floor.${floor.level}.${k}`] = { ...p, key: `floor.${floor.level}.${k}` };
    }
  }
  for (const [key, p] of Object.entries(scenario.overrides)) {
    if (p.status === "FIXED") throw new Error(`override ${key}: a scenario cannot create FIXED values`);
    if (!(key in params)) throw new Error(`override ${key}: unknown parameter`);
    params[key] = p;
  }
  for (const p of Object.values(params)) {
    if (p.status === "FIXED" && (p.evidence.length === 0 || !p.approvalId)) {
      flags.push({ severity: "BLOCK", code: "FIXED_WITHOUT_EVIDENCE", nodeId: p.key, message: `${p.key} is FIXED but lacks evidence/approval` });
    }
  }
  const numbers = Object.fromEntries(Object.entries(params).map(([k, p]) => [k, p.value]));
  return { params, numbers, flags };
}

/** Canonical JSON: sorted keys, so the hash is independent of insertion order. */
function canonical(x: unknown): string {
  if (Array.isArray(x)) return `[${x.map(canonical).join(",")}]`;
  if (x && typeof x === "object") {
    return `{${Object.keys(x).sort().map((k) => `${JSON.stringify(k)}:${canonical((x as Record<string, unknown>)[k])}`).join(",")}}`;
  }
  return JSON.stringify(x);
}

export function inputHash(numbers: Record<string, number>): string {
  return createHash("sha256").update(ENGINE_VERSION).update(canonical(numbers)).digest("hex");
}

export function run(model: BuildingModel, scenario: Scenario): CalcRun {
  const graph = buildGraph(model);
  const r = resolve(model, scenario);
  const values = graph.evaluate(r.numbers);
  const outputs = Object.fromEntries([...graph.nodes.keys()].sort().map((id) => [id, values[id]]));
  const flags = [...r.flags];

  for (const l of podiumLevels(model)) {
    const h = outputs[`floor.${l}.area_headroom_m2`];
    if (h < 0) flags.push({ severity: "BLOCK", code: "AREA_SHORTFALL", nodeId: `floor.${l}.area_headroom_m2`, message: `${l}: option needs ${-h} m2 more than the floor has` });
  }
  if (outputs["parking.shortfall"] > 0) {
    flags.push({ severity: "WARN", code: "PARKING_SHORTFALL", nodeId: "parking.shortfall", message: `parking short by ${outputs["parking.shortfall"]} stalls (assumed ratios)` });
  }
  if (outputs["profit"] < 0) flags.push({ severity: "WARN", code: "NEGATIVE_PROFIT", nodeId: "profit", message: "profit is negative" });

  return { engineVersion: ENGINE_VERSION, inputHash: inputHash(r.numbers), scenarioId: scenario.id, outputs, flags };
}

/** What changes if we move from scenario A to B? Pure graph + arithmetic. */
export function impact(model: BuildingModel, a: Scenario, b: Scenario, materiality = 0.005): ImpactReport {
  const graph = buildGraph(model);
  const ra = resolve(model, a), rb = resolve(model, b);
  const changedInputs = Object.keys(rb.numbers).filter((k) => ra.numbers[k] !== rb.numbers[k]).sort();
  const impactedNodes = graph.downstream(changedInputs);
  const va = graph.evaluate(ra.numbers), vb = graph.evaluate(rb.numbers);

  const deltas: ImpactReport["deltas"] = {};
  const roles = new Set<AiRole>();
  for (const id of impactedNodes) {
    if (va[id] === vb[id]) continue;
    deltas[id] = { before: va[id], after: vb[id] };
    const rel = Math.abs(vb[id] - va[id]) / Math.max(1, Math.abs(va[id]));
    if (rel >= materiality) for (const role of graph.nodes.get(id)!.reviewRoles ?? []) roles.add(role);
  }
  for (const floor of model.floors) {
    const before = a.selections[floor.level] ?? floor.currentUse;
    const after = b.selections[floor.level] ?? floor.currentUse;
    if (before !== after) for (const role of model.optionCatalog[after].reviewRoles) roles.add(role);
  }
  return { changedInputs, impactedNodes, deltas, reviewRoles: [...roles].sort() };
}
