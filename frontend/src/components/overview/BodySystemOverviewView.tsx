import { useMemo, useState } from "react";
import type { ContextRef } from "../../types/chat";
import { useBodySystems } from "../../hooks/useReportOverviews";
import { FULL_REPORT_ASK } from "../../lib/bodySystems";
import { shortDate } from "../marker/TrendChart";
import { ReportPicker } from "./ReportPicker";
import { SystemCard } from "./SystemCard";
import { SystemDetail } from "./SystemDetail";
import { t } from "../../i18n";

/**
 * The first thing a member sees after tapping Blood Report. Built from the report's structured
 * data, so it appears at once and never waits on a model. Only systems with results get a card.
 */
export function BodySystemOverviewView({
  onAsk,
  onClose,
}: {
  onAsk: (text: string, contextRef: ContextRef) => void;
  onClose: () => void;
}) {
  const [reportId, setReportId] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const query = useBodySystems(reportId);
  const data = query.data;
  const results = useMemo(() => new Map((data?.results ?? []).map((r) => [r.result_id, r])), [data]);

  const explainAll = () => onAsk(FULL_REPORT_ASK.text, FULL_REPORT_ASK.contextRef);

  if (query.isLoading) {
    return (
      <section className="overview" aria-busy="true" aria-live="polite">
        <p className="muted">{t("ui.overview.loading_blood", "Opening your blood report…")}</p>
      </section>
    );
  }
  if (query.isError || !data) {
    return (
      <section className="overview" role="alert">
        <p>{t("ui.overview.blood_unavailable", "I couldn't open the visual overview just now.")}</p>
        <div className="chips">
          <button type="button" onClick={explainAll}>
            {t("ui.overview.explain_in_chat", "Explain my blood report in chat")}
          </button>
          <button type="button" onClick={() => void query.refetch()}>
            {t("ui.overview.try_again", "Try again")}
          </button>
        </div>
      </section>
    );
  }

  const systems = [...data.systems ?? [], ...(data.allergy ? [data.allergy] : [])];
  const open = systems.find((s) => s.id === openId) || null;
  const pick = (ids: string[] | undefined) => (ids ?? []).map((id) => results.get(id)).filter((r): r is NonNullable<typeof r> => Boolean(r));

  if (open) {
    return (
      <div className="overview">
        <SystemDetail
          system={open}
          results={pick(open.result_ids)}
          related={pick(open.related_result_ids)}
          reportId={data.report?.report_id}
          onBack={() => setOpenId(null)}
          onAsk={onAsk}
        />
      </div>
    );
  }

  const totals = data.totals;
  return (
    <section className="overview" aria-labelledby="overview-title">
      <div className="overview-head">
        <div>
          <h2 id="overview-title">{t("ui.overview.blood_title", "Your blood report")}</h2>
          {data.report ? (
            <p className="muted">
              {t("ui.overview.report_dated", "Report dated")} {shortDate(data.report.report_date)}
              {totals ? ` · ${totals.unique_results} ${totals.unique_results === 1 ? "result" : "results"}` : ""}
              {totals && totals.abnormal > 0 ? ` · ${totals.abnormal} ${t("ui.overview.outside_range", "outside range")}` : ""}
            </p>
          ) : null}
        </div>
        <button type="button" className="overview-close" onClick={onClose}>
          {t("ui.overview.close", "Close")}
        </button>
      </div>
      <ReportPicker reports={data.available_reports ?? []} selectedId={data.report?.report_id} onSelect={(id) => { setOpenId(null); setReportId(id); }} />
      {data.state !== "ready" || systems.length === 0 ? (
        <p>{t("ui.overview.no_results", "There are no results on this report to show yet.")}</p>
      ) : (
        <ul className="system-grid" aria-label={t("ui.overview.systems", "Body systems with results")}>
          {systems.map((system) => (
            <SystemCard key={system.id} system={system} onOpen={setOpenId} />
          ))}
        </ul>
      )}
      <p className="muted overview-foot">
        {t("ui.overview.foot", "Only tests on this report are shown. A test that is not here has not been assessed.")}
      </p>
      <div className="chips">
        <button type="button" onClick={explainAll}>
          {t("ui.overview.explain_whole", "Explain my whole report")}
        </button>
      </div>
    </section>
  );
}
