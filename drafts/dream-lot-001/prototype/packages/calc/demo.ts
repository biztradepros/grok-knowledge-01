// CLICK 1: 3F, CLICK 2: KM36 -> what the UI would receive.
import { impact, run } from "./engine.ts";
import { loadModel, loadScenario } from "./load.ts";

const eok = (v: number) => `${(v / 1e8).toFixed(1)}억`;
const model = loadModel();
const base = loadScenario("base-132");
for (const name of ["base-132", "km36-3f", "km40-3f", "b3"]) {
  const r = run(model, loadScenario(name));
  const o = r.outputs;
  console.log(`\n== ${r.scenarioId}  hash=${r.inputHash.slice(0, 12)}  ${r.engineVersion}`);
  console.log(`총사업비 ${eok(o["cost.total"])} | 총수입 ${eok(o["rev.total"])} | 이익 ${eok(o["profit"])} | 이익률 ${(o["profit.rate_on_cost"] * 100).toFixed(1)}% | BEP 민간분양률 ${(o["bep.private_sale_rate"] * 100).toFixed(1)}% | 주차 ${o["parking.supplied"]}/${o["parking.required"]}`);
  for (const f of r.flags) console.log(`  [${f.severity}] ${f.code}: ${f.message}`);
}
const imp = impact(model, base, loadScenario("km36-3f"));
console.log("\n== IMPACT BASE-132 -> KM36-3F");
console.log("changed inputs:", imp.changedInputs.join(", "));
console.log("impacted nodes:", imp.impactedNodes.join(" → "));
console.log("review roles :", imp.reviewRoles.join(", "));
