import { describe, expect, it } from "vitest";
import { breakdownSegments, orderResults, outsideRange, systemAsks, systemSummaryLine } from "./bodySystems";
import type { BiomarkerResult, SystemSummary } from "../types/bodySystems";

const zero = { normal: 0, low: 0, high: 0, critical: 0, no_range: 0, no_value: 0 };
const sys = (over: Partial<SystemSummary>) => ({ id: "x", name: "Liver Health", scope: "primary", available_count: 0, abnormal_count: 0, status_breakdown: zero, state: "all_in_range", ...over }) as SystemSummary;
const res = (over: Partial<BiomarkerResult>) => ({ result_id: "1", display_name: "A", original_name: "A", status: "normal", history: [], secondary_system_ids: [], conflicting_values: [], ...over }) as BiomarkerResult;

describe("systemSummaryLine", () => {
  it("states counts without hardcoded numbers", () => {
    expect(systemSummaryLine(sys({ available_count: 1, status_breakdown: { ...zero, normal: 1 } }))).toBe("1 result · all within range");
    expect(systemSummaryLine(sys({ available_count: 7, status_breakdown: { ...zero, normal: 5, high: 2 } }))).toBe("7 results · 2 outside range");
  });
  it("never calls unassessed results normal", () => {
    expect(systemSummaryLine(sys({ available_count: 3, status_breakdown: { ...zero, normal: 1, no_range: 1, no_value: 1 } }))).toBe("3 results · 1 within range · 2 not assessed");
    expect(systemSummaryLine(sys({ available_count: 1, status_breakdown: { ...zero, no_value: 1 } }))).toBe("1 result · 1 not assessed");
  });
});

describe("breakdownSegments", () => {
  it("drops empty statuses and keeps a fixed reading order", () => {
    expect(breakdownSegments({ ...zero, normal: 2, critical: 1, no_value: 1 }).map((s) => s.key)).toEqual(["critical", "normal", "no_value"]);
    expect(breakdownSegments(zero)).toEqual([]);
  });
  it("counts out of range across low, high and critical", () => {
    expect(outsideRange({ ...zero, low: 1, high: 2, critical: 1 })).toBe(4);
  });
});

describe("orderResults", () => {
  it("puts critical first, then the largest gap, then in range, then unassessed", () => {
    const out = orderResults([
      res({ display_name: "Norm", status: "normal" }),
      res({ display_name: "NoVal", status: "no_value" }),
      res({ display_name: "Small", status: "high", value: 105, reference_high: 100 }),
      res({ display_name: "Big", status: "high", value: 200, reference_high: 100 }),
      res({ display_name: "Crit", status: "critical", value: 150, reference_high: 100 }),
    ]);
    expect(out.map((r) => r.display_name)).toEqual(["Crit", "Big", "Small", "Norm", "NoVal"]);
  });
});

describe("systemAsks", () => {
  it("names the results and adds the outside-range question only when something is outside range", () => {
    const quiet = systemAsks(sys({}), [res({ display_name: "ALT" })], "r1");
    expect(quiet.map((a) => a.id)).toEqual(["explain", "next"]);
    const flagged = systemAsks(sys({ abnormal_count: 1 }), [res({ display_name: "ALT", status: "high" })], "r1");
    expect(flagged.map((a) => a.id)).toEqual(["explain", "outside", "next"]);
    expect(flagged[0].text).toContain("ALT");
    expect(flagged[0].contextRef).toMatchObject({ type: "blood_report", report_id: "r1" });
  });
});
