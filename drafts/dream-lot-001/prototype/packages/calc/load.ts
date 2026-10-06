import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import type { BuildingModel, Scenario } from "../core/types.ts";

const dir = fileURLToPath(new URL("../../scenarios/", import.meta.url));
export const loadModel = (): BuildingModel => JSON.parse(readFileSync(dir + "model.daeheung.dummy.json", "utf8"));
export const loadScenario = (name: string): Scenario => JSON.parse(readFileSync(dir + name + ".json", "utf8"));
