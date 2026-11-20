import type { ContextRef } from "../../types/chat";
import type { BiomarkerResult } from "../../types/bodySystems";
import { systemName } from "./systemNames";
import { resultAsks, statusDisplay } from "../../lib/bodySystems";
import { fmt, formatBounds } from "../../lib/range";
import { RangeBar } from "../messages/RangeBar";
import { TrendChart, shortDate } from "../marker/TrendChart";
import { AskCuraActions } from "./AskCuraActions";
import { t } from "../../i18n";

const TREND_TEXT: Record<string, string> = {
  toward_range: "Moving toward the reference range since your last report",
  away_from_range: "Moving away from the reference range since your last report",
  steady: "About the same as your last report",
  in_range: "Within the reference range",
};

/** Everything the report says about one result, with its history only where it is comparable. */
export function BiomarkerDetail({ item, onAsk }: { item: BiomarkerResult; onAsk: (text: string, contextRef: ContextRef) => void }) {
  const bounds = formatBounds(item.reference_low, item.reference_high, item.unit);
  const history = item.history ?? [];
  const related = (item.secondary_system_ids ?? []).map(systemName);
  return (
    <div className="biomarker-detail">
      {item.value != null ? (
        <RangeBar label={item.display_name} value={item.value} unit={item.unit} low={item.reference_low} high={item.reference_high} />
      ) : (
        <p className="muted">{t("ui.overview.no_numeric_result", "This report has no numeric result for this test.")}</p>
      )}
      {item.value != null && !bounds ? <p className="muted">{t("ui.overview.no_range_given", "The report gives no reference range for this test, so it is not marked as in or out of range.")}</p> : null}
      <dl className="biomarker-facts">
        {item.measured_on ? (
          <div>
            <dt>{t("ui.overview.measured", "Measured")}</dt>
            <dd>{shortDate(item.measured_on)}</dd>
          </div>
        ) : null}
        {item.source_group ? (
          <div>
            <dt>{t("ui.overview.test_group", "Test group")}</dt>
            <dd>{item.source_group}</dd>
          </div>
        ) : null}
        {item.original_name !== item.display_name ? (
          <div>
            <dt>{t("ui.overview.lab_name", "Name on the report")}</dt>
            <dd>{item.original_name}</dd>
          </div>
        ) : null}
        {item.previous_value != null ? (
          <div>
            <dt>{t("ui.overview.previous", "Previous")}</dt>
            <dd>
              {fmt(item.previous_value)}
              {item.unit ? ` ${item.unit}` : ""}
              {item.previous_on ? ` · ${shortDate(item.previous_on)}` : ""}
            </dd>
          </div>
        ) : null}
      </dl>
      {item.trend ? <p className="marker-panel-trend">{TREND_TEXT[item.trend]}</p> : null}
      {history.length >= 2 ? (
        <TrendChart label={item.display_name} unit={item.unit} points={history} low={item.reference_low} high={item.reference_high} />
      ) : (
        <p className="muted">{t("ui.overview.one_result_so_far", "Only one comparable result so far. A trend appears after your next report.")}</p>
      )}
      {item.history_note ? <p className="muted">{item.history_note}</p> : null}
      {related.length ? (
        <p className="muted">
          {t("ui.overview.also_relevant_to", "Also relevant to")}: {related.join(", ")}
        </p>
      ) : null}
      {item.is_derived ? <p className="muted">{t("ui.overview.derived", "This is a calculated value taken from your report as given.")}</p> : null}
      {(item.conflicting_values ?? []).length > 0 ? (
        <p className="overview-note" role="note">
          {t("ui.overview.conflict", "This test appears more than once in this report with different values")}: {item.conflicting_values!.map(fmt).join(", ")}
          {item.unit ? ` ${item.unit}` : ""}. {t("ui.overview.conflict_tail", "The first one is shown.")}
        </p>
      ) : null}
      {item.note ? <p className="muted">{item.note}</p> : null}
      <p className="muted">{statusDisplay(item.status).label}</p>
      <AskCuraActions actions={resultAsks(item)} onAsk={onAsk} label={`${t("ui.overview.ask_cura_about", "Ask CURA about")} ${item.display_name}`} />
    </div>
  );
}
