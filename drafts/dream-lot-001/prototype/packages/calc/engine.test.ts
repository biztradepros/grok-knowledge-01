import { test } from "node:test";
import assert from "node:assert/strict";
import { impact, run } from "./engine.ts";
import { guardAiText, renderAiText } from "./guard.ts";
import { buildGraph } from "./model.ts";
import { CalcGraph } from "./graph.ts";
import { loadModel, loadScenario } from "./load.ts";

const model = loadModel();

test("same input -> same output and hash (determinism)", () => {
  const a = run(model, loadScenario("base-132"));
  const b = run(loadModel(), loadScenario("base-132"));
  assert.deepEqual(a, b);
  assert.match(a.inputHash, /^[0-9a-f]{64}$/);
});

test("different scenario -> different hash", () => {
  assert.notEqual(run(model, loadScenario("base-132")).inputHash, run(model, loadScenario("km36-3f")).inputHash);
});

test("3F -> KM36 propagates to profit/BEP and calls medical+legal+MEP reviewers", () => {
  const imp = impact(model, loadScenario("base-132"), loadScenario("km36-3f"));
  for (const id of ["floor.3F.area_headroom_m2", "podium.fitout_capex", "parking.required", "cost.finance", "profit", "bep.private_sale_rate"]) {
    assert.ok(imp.impactedNodes.includes(id), `expected ${id} impacted`);
  }
  assert.ok(!imp.impactedNodes.includes("rev.lh"), "LH revenue does not depend on 3F");
  for (const r of ["MEDICAL_RESEARCHER", "LEGAL_RESEARCHER", "MEP_FIRE_REVIEWER"]) assert.ok(imp.reviewRoles.includes(r as never));
});

test("KM40 on a 950m2 floor is blocked (area shortfall), KM36 is not", () => {
  assert.ok(run(model, loadScenario("km40-3f")).flags.some((f) => f.code === "AREA_SHORTFALL" && f.severity === "BLOCK"));
  assert.ok(!run(model, loadScenario("km36-3f")).flags.some((f) => f.code === "AREA_SHORTFALL"));
});

test("B3 adds basement cost and parking supply", () => {
  const base = run(model, loadScenario("base-132")).outputs;
  const b3 = run(model, loadScenario("b3")).outputs;
  assert.ok(b3["cost.basement_extra"] > 0 && base["cost.basement_extra"] === 0);
  assert.ok(b3["parking.supplied"] > base["parking.supplied"]);
  assert.ok(b3["cost.finance"] > base["cost.finance"]);
});

test("scenario cannot smuggle in FIXED values", () => {
  const s = loadScenario("b3");
  s.overrides["basement.levels"].status = "FIXED" as never;
  assert.throws(() => run(model, s), /cannot create FIXED/);
});

test("FIXED without evidence is a BLOCK flag", () => {
  const m = loadModel();
  m.params["cost.land"].status = "FIXED";
  assert.ok(run(m, loadScenario("base-132")).flags.some((f) => f.code === "FIXED_WITHOUT_EVIDENCE"));
});

test("cycles are rejected", () => {
  assert.throws(() => new CalcGraph([
    { id: "a", label: "a", unit: "KRW", deps: ["b"], compute: (v) => v("b") },
    { id: "b", label: "b", unit: "KRW", deps: ["a"], compute: (v) => v("a") },
  ]), /cycle/);
});

test("upstream lineage of profit reaches land cost (evidence view)", () => {
  assert.ok(buildGraph(model).upstream("profit").includes("cost.land"));
});

test("AI guard: placeholders pass, invented numbers fail", () => {
  const r = run(model, loadScenario("base-132"));
  const ok = guardAiText("KM36 전환 시 이익은 [[profit]] 입니다.", r);
  assert.ok(ok.ok);
  assert.match(renderAiText("이익 [[profit]]", r), /억/);
  const realEok = (r.outputs["profit"] / 1e8).toFixed(1);
  assert.ok(guardAiText(`이익은 약 ${realEok}억`, r).ok);
  const bad = guardAiText("이익은 약 999.9억 입니다", r);
  assert.equal(bad.ok, false);
  assert.deepEqual(bad.unmatchedNumbers, ["999.9억"]);
  assert.equal(guardAiText("[[made.up]]", r).ok, false);
});
