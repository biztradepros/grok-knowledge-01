// Generic reactive calculation DAG. Domain-free: Vertical A can reuse it as-is.
// Inputs are leaf ids (parameter keys). Calc nodes declare deps explicitly so the
// impact of any change is a pure graph query — no LLM involved.

import type { AiRole, Unit } from "../core/types.ts";

export interface CalcNode {
  id: string;
  label: string;
  unit: Unit;
  deps: string[];                          // input keys or other node ids
  compute: (v: (id: string) => number) => number;
  reviewRoles?: AiRole[];                  // who must look when this node moves materially
}

export class CalcGraph {
  readonly nodes = new Map<string, CalcNode>();
  private order: string[] = [];
  private dependents = new Map<string, Set<string>>();

  constructor(nodes: CalcNode[]) {
    for (const n of nodes) {
      if (this.nodes.has(n.id)) throw new Error(`duplicate node ${n.id}`);
      this.nodes.set(n.id, n);
    }
    for (const n of nodes) {
      for (const d of n.deps) {
        if (!this.dependents.has(d)) this.dependents.set(d, new Set());
        this.dependents.get(d)!.add(n.id);
      }
    }
    this.order = this.topoSort();
  }

  /** Kahn's algorithm; throws on cycles. Ties broken by id for determinism. */
  private topoSort(): string[] {
    const indeg = new Map<string, number>();
    for (const n of this.nodes.values()) {
      indeg.set(n.id, n.deps.filter((d) => this.nodes.has(d)).length);
    }
    const ready = [...indeg].filter(([, d]) => d === 0).map(([id]) => id).sort();
    const out: string[] = [];
    while (ready.length) {
      const id = ready.shift()!;
      out.push(id);
      for (const dep of [...(this.dependents.get(id) ?? [])].sort()) {
        const left = indeg.get(dep)! - 1;
        indeg.set(dep, left);
        if (left === 0) { ready.push(dep); ready.sort(); }
      }
    }
    if (out.length !== this.nodes.size) {
      const stuck = [...indeg].filter(([, d]) => d > 0).map(([id]) => id);
      throw new Error(`cycle detected among: ${stuck.join(", ")}`);
    }
    return out;
  }

  /** Every node downstream of the given inputs/nodes, in evaluation order. */
  downstream(changed: string[]): string[] {
    const seen = new Set<string>();
    const stack = [...changed];
    while (stack.length) {
      const id = stack.pop()!;
      for (const d of this.dependents.get(id) ?? []) {
        if (!seen.has(d)) { seen.add(d); stack.push(d); }
      }
    }
    return this.order.filter((id) => seen.has(id));
  }

  /** Upstream lineage of a node — used by EVIDENCE VIEW ("why is this number X?"). */
  upstream(id: string): string[] {
    const seen = new Set<string>();
    const stack = [id];
    while (stack.length) {
      const cur = stack.pop()!;
      for (const d of this.nodes.get(cur)?.deps ?? []) {
        if (!seen.has(d)) { seen.add(d); stack.push(d); }
      }
    }
    return [...seen].sort();
  }

  evaluate(inputs: Record<string, number>): Record<string, number> {
    const values: Record<string, number> = { ...inputs };
    const get = (id: string): number => {
      const v = values[id];
      if (v === undefined || Number.isNaN(v)) throw new Error(`missing value: ${id}`);
      return v;
    };
    for (const id of this.order) {
      const v = this.nodes.get(id)!.compute(get);
      if (!Number.isFinite(v)) throw new Error(`non-finite result at ${id}`);
      values[id] = v;
    }
    return values;
  }

  /** Edges for the FLOW VIEW (React Flow): input → node, node → node. */
  edges(): { source: string; target: string }[] {
    const out: { source: string; target: string }[] = [];
    for (const id of this.order) {
      for (const d of this.nodes.get(id)!.deps) out.push({ source: d, target: id });
    }
    return out;
  }
}
