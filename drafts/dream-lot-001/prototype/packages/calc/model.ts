// Daeheung domain pack: turns a BuildingModel into a CalcGraph.
// Formulas are deliberately simple and readable. Each one is a reviewable,
// versioned piece of code — NOT a prompt. Changing a formula bumps ENGINE_VERSION.

import type { BuildingModel } from "../core/types.ts";
import { CalcGraph, type CalcNode } from "./graph.ts";

export const ENGINE_VERSION = "daeheung-calc@0.1.0";

const won = (x: number) => Math.round(x);              // money: integer KRW
const ratio = (x: number) => Math.round(x * 1e6) / 1e6; // ratios: 6 dp

/** Inputs per podium slot that the selected MD option supplies. */
export const SLOT_KEYS = ["required_area_m2", "fitout_capex", "annual_rent", "parking_per_100m2"] as const;

export function podiumLevels(model: BuildingModel): string[] {
  return model.floors.map((f) => f.level).sort();
}

export function buildGraph(model: BuildingModel): CalcGraph {
  const levels = podiumLevels(model);
  const f = (l: string, k: string) => `floor.${l}.${k}`;
  const nodes: CalcNode[] = [];

  // --- slot level ---------------------------------------------------------
  for (const l of levels) {
    nodes.push({
      id: f(l, "area_headroom_m2"), label: `${l} 면적 여유`, unit: "M2",
      deps: [f(l, "area"), f(l, "required_area_m2")],
      compute: (v) => ratio(v(f(l, "area")) - v(f(l, "required_area_m2"))),
      reviewRoles: ["ARCHITECTURE_RESEARCHER"],
    });
  }
  const sum = (id: string, label: string, unit: CalcNode["unit"], key: string, fn: (x: number) => number) =>
    nodes.push({ id, label, unit, deps: levels.map((l) => f(l, key)), compute: (v) => fn(levels.reduce((s, l) => s + v(f(l, key)), 0)) });

  sum("podium.fitout_capex", "저층부 MD 공사/TI", "KRW", "fitout_capex", won);
  sum("podium.annual_rent", "저층부 연 임대수익", "KRW", "annual_rent", won);
  sum("podium.gfa_m2", "저층부 연면적", "M2", "area", ratio);

  nodes.push(
    { id: "podium.value", label: "저층부 가치(환원)", unit: "KRW", deps: ["podium.annual_rent", "podium.cap_rate"],
      compute: (v) => won(v("podium.annual_rent") / v("podium.cap_rate")), reviewRoles: ["FINANCE_RESEARCHER"] },
    { id: "parking.podium_required", label: "저층부 법정주차(가정)", unit: "STALLS",
      deps: levels.flatMap((l) => [f(l, "area"), f(l, "parking_per_100m2")]),
      compute: (v) => ratio(levels.reduce((s, l) => s + (v(f(l, "area")) * v(f(l, "parking_per_100m2"))) / 100, 0)) },
    { id: "parking.res_required", label: "주거 주차(가정)", unit: "STALLS", deps: ["units.lh", "units.private", "res.parking_per_unit"],
      compute: (v) => ratio((v("units.lh") + v("units.private")) * v("res.parking_per_unit")) },
    { id: "parking.required", label: "필요 주차", unit: "STALLS", deps: ["parking.podium_required", "parking.res_required"],
      compute: (v) => Math.ceil(v("parking.podium_required") + v("parking.res_required")) },
    { id: "parking.supplied", label: "공급 주차", unit: "STALLS", deps: ["basement.levels", "basement.stalls_per_level"],
      compute: (v) => v("basement.levels") * v("basement.stalls_per_level") },
    { id: "parking.shortfall", label: "주차 부족", unit: "STALLS", deps: ["parking.required", "parking.supplied"],
      compute: (v) => Math.max(0, v("parking.required") - v("parking.supplied")), reviewRoles: ["PARKING_REVIEWER", "LEGAL_RESEARCHER"] },

    // --- cost -------------------------------------------------------------
    { id: "gfa.above_m2", label: "지상 연면적", unit: "M2", deps: ["res.gfa_m2", "podium.gfa_m2"],
      compute: (v) => ratio(v("res.gfa_m2") + v("podium.gfa_m2")) },
    { id: "gfa.basement_m2", label: "지하 연면적", unit: "M2", deps: ["basement.levels", "basement.area_per_level_m2"],
      compute: (v) => ratio(v("basement.levels") * v("basement.area_per_level_m2")) },
    { id: "cost.basement_extra", label: "B3 이하 추가 토목", unit: "KRW", deps: ["basement.levels", "basement.extra_cost_per_level_over_2"],
      compute: (v) => won(Math.max(0, v("basement.levels") - 2) * v("basement.extra_cost_per_level_over_2")),
      reviewRoles: ["CONSTRUCTION_REVIEWER"] },
    { id: "cost.construction", label: "공사비", unit: "KRW",
      deps: ["gfa.above_m2", "cost.above_per_m2", "gfa.basement_m2", "cost.basement_per_m2", "cost.basement_extra"],
      compute: (v) => won(v("gfa.above_m2") * v("cost.above_per_m2") + v("gfa.basement_m2") * v("cost.basement_per_m2") + v("cost.basement_extra")),
      reviewRoles: ["CONSTRUCTION_REVIEWER"] },
    { id: "cost.direct", label: "직접비", unit: "KRW", deps: ["cost.construction", "podium.fitout_capex"],
      compute: (v) => won(v("cost.construction") + v("podium.fitout_capex")) },
    { id: "cost.soft", label: "간접비", unit: "KRW", deps: ["cost.direct", "cost.soft_ratio"],
      compute: (v) => won(v("cost.direct") * v("cost.soft_ratio")) },
    { id: "finance.pf_amount", label: "PF 규모", unit: "KRW", deps: ["cost.land", "cost.direct", "cost.soft", "finance.pf_ltc"],
      compute: (v) => won((v("cost.land") + v("cost.direct") + v("cost.soft")) * v("finance.pf_ltc")) },
    { id: "cost.finance", label: "금융비", unit: "KRW",
      deps: ["finance.pf_amount", "finance.pf_rate", "finance.pf_years", "finance.avg_drawdown"],
      compute: (v) => won(v("finance.pf_amount") * v("finance.pf_rate") * v("finance.pf_years") * v("finance.avg_drawdown")),
      reviewRoles: ["FINANCE_RESEARCHER"] },
    { id: "cost.total", label: "총사업비", unit: "KRW", deps: ["cost.land", "cost.direct", "cost.soft", "cost.finance"],
      compute: (v) => won(v("cost.land") + v("cost.direct") + v("cost.soft") + v("cost.finance")) },

    // --- revenue / result ---------------------------------------------------
    { id: "rev.private", label: "민간 분양수입", unit: "KRW", deps: ["units.private", "price.private_per_unit"],
      compute: (v) => won(v("units.private") * v("price.private_per_unit")) },
    { id: "rev.lh", label: "LH 매입수입", unit: "KRW", deps: ["units.lh", "price.lh_per_unit"],
      compute: (v) => won(v("units.lh") * v("price.lh_per_unit")) },
    { id: "rev.total", label: "총수입", unit: "KRW", deps: ["rev.private", "rev.lh", "podium.value"],
      compute: (v) => won(v("rev.private") + v("rev.lh") + v("podium.value")) },
    { id: "profit", label: "사업이익", unit: "KRW", deps: ["rev.total", "cost.total"],
      compute: (v) => won(v("rev.total") - v("cost.total")), reviewRoles: ["FINANCE_RESEARCHER", "CHALLENGER"] },
    { id: "profit.rate_on_cost", label: "총사업비 대비 이익률", unit: "RATIO", deps: ["profit", "cost.total"],
      compute: (v) => ratio(v("profit") / v("cost.total")) },
    { id: "bep.private_sale_rate", label: "BEP 민간 분양률", unit: "RATIO", deps: ["cost.total", "rev.lh", "podium.value", "rev.private"],
      compute: (v) => ratio((v("cost.total") - v("rev.lh") - v("podium.value")) / v("rev.private")),
      reviewRoles: ["FINANCE_RESEARCHER"] },
  );
  return new CalcGraph(nodes);
}
