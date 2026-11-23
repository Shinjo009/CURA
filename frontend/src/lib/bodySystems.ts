import type { ContextRef } from "../types/chat";
import type { BiomarkerResult, RiskGroupSummary, RiskResult, StatusBreakdown, SystemSummary } from "../types/bodySystems";
import { t } from "../i18n";

export const OUT_OF_RANGE = new Set(["low", "high", "critical"]);

const STATUS_TEXT: Record<string, { icon: string; label: string }> = {
  normal: { icon: "✓", label: "Within range" },
  low: { icon: "▼", label: "Below range" },
  high: { icon: "▲", label: "Above range" },
  critical: { icon: "!", label: "Critical" },
  no_range: { icon: "•", label: "No reference range" },
  no_value: { icon: "○", label: "No result" },
};

export function statusDisplay(status: string): { icon: string; label: string } {
  return STATUS_TEXT[status] || { icon: "•", label: "Not assessed" };
}

export function outsideRange(counts: StatusBreakdown | undefined): number {
  return (counts?.low ?? 0) + (counts?.high ?? 0) + (counts?.critical ?? 0);
}

function plural(n: number, one: string, many: string): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** One line that states what the card holds, built only from its counts. */
export function systemSummaryLine(system: SystemSummary): string {
  const counts = system.status_breakdown;
  const parts = [plural(system.available_count, t("ui.overview.result", "result"), t("ui.overview.results", "results"))];
  const out = outsideRange(counts);
  if (out > 0) parts.push(`${out} ${t("ui.overview.outside_range", "outside range")}`);
  else if (counts.normal === system.available_count) parts.push(t("ui.overview.all_within_range", "all within range"));
  else if (counts.normal > 0) parts.push(`${counts.normal} ${t("ui.overview.within_range", "within range")}`);
  const unassessed = counts.no_range + counts.no_value;
  if (unassessed > 0 && out === 0 && counts.normal !== system.available_count) {
    parts.push(`${unassessed} ${t("ui.overview.not_assessed", "not assessed")}`);
  }
  return parts.join(" · ");
}

export type Segment = { key: string; count: number; label: string };

/** Breakdown segments in a fixed reading order, empty ones dropped. */
export function breakdownSegments(counts: StatusBreakdown): Segment[] {
  const order: Array<[keyof StatusBreakdown, string]> = [
    ["critical", "Critical"],
    ["high", "Above range"],
    ["low", "Below range"],
    ["normal", "Within range"],
    ["no_range", "No reference range"],
    ["no_value", "No result"],
  ];
  return order.filter(([key]) => counts[key] > 0).map(([key, label]) => ({ key, count: counts[key], label }));
}

const RANK: Record<string, number> = { critical: 0, high: 1, low: 1, no_range: 3, no_value: 4, normal: 2 };

function gap(item: BiomarkerResult): number {
  if (item.value == null) return 0;
  if (item.reference_high != null && item.value > item.reference_high && item.reference_high) return (item.value - item.reference_high) / Math.abs(item.reference_high);
  if (item.reference_low != null && item.value < item.reference_low && item.reference_low) return (item.reference_low - item.value) / Math.abs(item.reference_low);
  return 0;
}

/** Results needing attention first, then in range, then those the report could not assess. */
export function orderResults(results: BiomarkerResult[]): BiomarkerResult[] {
  return [...results].sort(
    (a, b) => (RANK[a.status] ?? 5) - (RANK[b.status] ?? 5) || gap(b) - gap(a) || a.display_name.localeCompare(b.display_name)
  );
}

export type AskAction = { id: string; label: string; text: string; contextRef: ContextRef };

function joinNames(names: string[]): string {
  if (names.length <= 1) return names.join("");
  return `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}`;
}

export function systemAsks(system: SystemSummary, results: BiomarkerResult[], reportId?: string | null): AskAction[] {
  const ordered = orderResults(results);
  const flagged = ordered.filter((item) => OUT_OF_RANGE.has(item.status)).slice(0, 3).map((item) => item.display_name);
  const focus = (flagged.length ? flagged : ordered.slice(0, 3).map((item) => item.display_name));
  // Result names stay in the question so chat knows which results are meant. The numbers do not.
  const especially = focus.length ? `, especially ${joinNames(focus)}` : "";
  const ref: ContextRef = { type: "blood_report", source: "supershyft", report_id: reportId ?? null };
  const asks: AskAction[] = [
    {
      id: "explain",
      label: t("ui.overview.explain_these", "Explain these results"),
      text: `Explain my ${system.name} results in simple words${especially}.`,
      contextRef: ref,
    },
  ];
  if (flagged.length > 0) {
    asks.push({
      id: "outside",
      label: t("ui.overview.what_is_outside_range", "What is outside range?"),
      text: `Why might my ${joinNames(flagged)} be outside the normal range?`,
      contextRef: ref,
    });
  }
  asks.push({
    id: "next",
    label: t("ui.overview.what_can_i_do", "What can I do?"),
    text: `What can I do to support my ${system.name}${especially}?`,
    contextRef: ref,
  });
  return asks;
}

export function resultAsks(item: BiomarkerResult): AskAction[] {
  const ref: ContextRef = { type: "blood_marker", source: "supershyft", marker_code: item.cura_key || item.canonical_id || item.display_name };
  const asks: AskAction[] = [
    { id: "mean", label: t("ui.overview.what_does_this_mean", "What does this mean?"), text: `What does my ${item.display_name} result mean?`, contextRef: ref },
  ];
  if ((item.history ?? []).length >= 2) {
    asks.push({ id: "change", label: t("ui.overview.how_has_it_changed", "How has it changed?"), text: `How has my ${item.display_name} changed over time?`, contextRef: ref });
  }
  if (OUT_OF_RANGE.has(item.status)) {
    asks.push({ id: "do", label: t("ui.overview.what_can_i_do", "What can I do?"), text: `What can I do about my ${item.display_name}?`, contextRef: ref });
  }
  return asks;
}

export function riskGroupAsks(group: RiskGroupSummary, risks: RiskResult[], reportId?: string | null): AskAction[] {
  const names = risks.slice(0, 6).map((r) => r.name);
  const ref: ContextRef = { type: "bio_ai_report", source: "supershyft", report_id: reportId ?? null };
  return [
    {
      id: "explain",
      label: t("ui.overview.explain_these_risks", "Explain these risks"),
      text: `Explain my ${group.name} Bio-AI results in simple words, especially ${joinNames(names.slice(0, 3))}.`,
      contextRef: ref,
    },
    {
      id: "lower",
      label: t("ui.overview.what_can_i_do", "What can I do?"),
      text: `What can I do to lower my ${group.name} risks, based on my Bio-AI report?`,
      contextRef: ref,
    },
  ];
}

export function riskAsks(risk: RiskResult, reportId?: string | null): AskAction[] {
  const ref: ContextRef = { type: "bio_ai_risk", source: "supershyft", risk_code: risk.code, report_id: reportId ?? null };
  return [
    { id: "mean", label: t("ui.overview.what_does_this_mean", "What does this mean?"), text: `What does my ${risk.name} risk result mean?`, contextRef: { ...ref, entry_point: "risk_explainer" } },
    { id: "do", label: t("ui.overview.what_can_i_do", "What can I do?"), text: `What can I do about my ${risk.name} risk?`, contextRef: ref },
  ];
}

export const FULL_REPORT_ASK: { text: string; contextRef: ContextRef } = {
  text: "What does my lab report say about my health?",
  contextRef: { type: "blood_report", source: "supershyft", entry_point: "blood_report_overview" },
};
export const FULL_BIO_AI_ASK: { text: string; contextRef: ContextRef } = {
  text: "Help me understand my latest Bio-AI report and its findings.",
  contextRef: { type: "bio_ai_report", source: "supershyft" },
};
