import type { SystemSummary } from "../../types/bodySystems";
import { systemSummaryLine } from "../../lib/bodySystems";
import { StatusBreakdownBar } from "./StatusBreakdownBar";
import { t } from "../../i18n";

/** One body system the member has results for. Opens that system's results. */
export function SystemCard({ system, onOpen }: { system: SystemSummary; onOpen: (id: string) => void }) {
  const line = systemSummaryLine(system);
  const findings = system.key_findings ?? [];
  const related = system.scope === "related_only";
  return (
    <li>
      <button
        type="button"
        className="system-card"
        data-state={system.state}
        aria-label={`${system.name}. ${line}. ${t("ui.overview.open_results", "Open results")}`}
        onClick={() => onOpen(system.id)}
      >
        <span className="system-card-name">{system.name}</span>
        {system.about ? <span className="system-card-about">{system.about}</span> : null}
        <span className="system-card-line">{line}</span>
        {related ? <span className="system-card-tag">{t("ui.overview.related_results", "Related results")}</span> : null}
        <StatusBreakdownBar counts={system.status_breakdown} name={system.name} />
        {findings.length > 0 ? (
          <span className="system-card-findings">
            {findings.map((f) => (
              <span key={f.result_id}>
                {f.label}
                {f.how_far ? ` · ${f.how_far} ${f.status === "low" ? "below" : "above"} range` : ""}
              </span>
            ))}
          </span>
        ) : null}
        {system.needs_mapping_review ? (
          <span className="system-card-tag">{t("ui.overview.not_yet_grouped", "Not yet grouped into a body system")}</span>
        ) : null}
      </button>
    </li>
  );
}
