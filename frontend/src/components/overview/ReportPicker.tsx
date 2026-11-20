import type { ReportRef } from "../../types/bodySystems";
import { t } from "../../i18n";

const LINE: Record<string, string> = { bio_ai: "Bio-AI", advanced_bio_ai: "Advanced Bio-AI" };

function format(ref: ReportRef): string {
  const d = new Date(`${ref.report_date.slice(0, 10)}T00:00:00`);
  const day = Number.isNaN(d.getTime()) ? ref.report_date : d.toLocaleDateString(undefined, { day: "numeric", month: "short", year: "numeric" });
  const line = ref.source_line ? LINE[ref.source_line] : undefined;
  return line ? `${day} · ${line}` : day;
}

/** Shown only when the member has more than one report. */
export function ReportPicker({
  reports,
  selectedId,
  onSelect,
}: {
  reports: ReportRef[];
  selectedId: string | null | undefined;
  onSelect: (reportId: string) => void;
}) {
  if (reports.length < 2) return null;
  return (
    <label className="overview-picker">
      <span>{t("ui.overview.report", "Report")}</span>
      <select value={selectedId ?? ""} onChange={(event) => onSelect(event.target.value)}>
        {reports.map((ref) => (
          <option key={ref.report_id} value={ref.report_id}>
            {format(ref)}
          </option>
        ))}
      </select>
    </label>
  );
}
