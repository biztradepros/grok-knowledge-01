// @dream/core — shared domain types for the Computable Building.
// The same Slot / Option / Scenario / Parameter / Evidence core is meant to be
// reused by Vertical A (product slots) — only the "domain pack" differs.

/** Where a number came from. DERIVED values are never stored as inputs. */
export type ParamStatus = "FIXED" | "ASSUMPTION" | "OPTION" | "DERIVED";

export type Unit = "KRW" | "KRW_PER_M2" | "KRW_PER_UNIT" | "M2" | "PYEONG" | "UNITS" | "STALLS" | "RATIO" | "YEARS" | "COUNT";

export interface EvidenceRef {
  evidenceId: string;
  /** e.g. "LH 공고 2026-xx p.3", "시공사 견적 v2 row 41" */
  locator?: string;
}

/** One input number. The ONLY place inputs live. */
export interface Parameter {
  key: string;              // e.g. "cost.above_ground_per_m2"
  value: number;
  unit: Unit;
  status: Exclude<ParamStatus, "DERIVED">;
  confidence: number;       // 0..1, human-set
  evidence: EvidenceRef[];  // FIXED requires >= 1 (enforced in DB + engine)
  approvalId?: string;      // FIXED requires an approval
  note?: string;
}

export type FloorLevel = string; // "B3" .. "15F"

export type FloorUseCode =
  | "LH_RES" | "PRIVATE_RES"
  | "KM30" | "KM36" | "KM40"
  | "ANCHOR_BAKERY" | "ANCHOR_RETAIL" | "COMMERCIAL"
  | "PARKING" | "MEP" | "LOBBY";

/** A selectable option for a slot (floor). params override base parameters while selected. */
export interface MdOption {
  code: FloorUseCode;
  label: string;
  /** floor-scoped parameter overrides; key is relative, engine prefixes "floor.<level>." */
  params: Record<string, Parameter>;
  /** roles that must review when this option is newly selected */
  reviewRoles: AiRole[];
}

export interface Floor {
  level: FloorLevel;
  grossAreaM2: Parameter;
  currentUse: FloorUseCode;
  status: Exclude<ParamStatus, "DERIVED">; // is the USE fixed, assumed, or open?
  options: FloorUseCode[];                 // allowed options for this slot
}

export interface BuildingModel {
  projectId: string;
  baseVersion: string;          // immutable snapshot id
  floors: Floor[];
  optionCatalog: Record<FloorUseCode, MdOption>;
  params: Record<string, Parameter>;
}

/** A scenario never copies the model: base version + selections + overrides. */
export interface Scenario {
  id: string;                   // "BASE-132", "KM36-3F", "B3"
  baseVersion: string;
  selections: Record<FloorLevel, FloorUseCode>;
  overrides: Record<string, Parameter>; // must be status OPTION or ASSUMPTION
  addedFloors?: Floor[];               // e.g. B3
}

export type AiRole =
  | "ARCHITECTURE_RESEARCHER" | "MEDICAL_RESEARCHER" | "LEGAL_RESEARCHER"
  | "FINANCE_RESEARCHER" | "CONSTRUCTION_REVIEWER" | "PARKING_REVIEWER"
  | "MEP_FIRE_REVIEWER" | "CHALLENGER" | "FACT_CHECKER" | "AI_COACH";

/** Output of one deterministic engine run. Persisted as calc_run. */
export interface CalcRun {
  engineVersion: string;
  inputHash: string;            // sha256 of canonical resolved inputs
  scenarioId: string;
  outputs: Record<string, number>;
  flags: CalcFlag[];
}

export interface CalcFlag {
  severity: "INFO" | "WARN" | "BLOCK";
  code: string;                 // "AREA_SHORTFALL", "PARKING_SHORTFALL", "FIXED_WITHOUT_EVIDENCE"
  nodeId: string;
  message: string;
}

export interface ImpactReport {
  changedInputs: string[];
  impactedNodes: string[];      // topologically ordered
  deltas: Record<string, { before: number; after: number }>;
  reviewRoles: AiRole[];
}
