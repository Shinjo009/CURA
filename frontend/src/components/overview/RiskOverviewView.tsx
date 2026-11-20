import { useState } from "react";
import type { ContextRef } from "../../types/chat";
import type { RiskGroupSummary, RiskResult } from "../../types/bodySystems";
import { useRiskOverview } from "../../hooks/useReportOverviews";
import { FULL_BIO_AI_ASK, riskAsks, riskGroupAsks } from "../../lib/bodySystems";
import { shortDate, TrendChart } from "../marker/TrendChart";
import { AskCuraActions } from "./AskCuraActions";
import { ReportPicker } from "./ReportPicker";
import { t } from "../../i18n";

function RiskRow({ risk, reportId, onAsk }: { risk: RiskResult; reportId?: string | null; onAsk: (text: string, ref: ContextRef) => void }) {
  const [open, setOpen] = useState(false);
  const points = (risk.history ?? []).filter((p) => typeof p.score === "number").map((p) => ({ date: p.date, value: p.score as number, status: p.status ?? undefined }));
  return (
    <li className="result-row" data-level={risk.level}>
      <button type="button" className="result-row-head" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span className="result-row-name">
          {risk.name}
          <span className="result-row-group">{t("ui.overview.predicted_risk", "Predicted risk")}</span>
        </span>
        <span className="result-row-value">{risk.score != null ? `Score ${risk.score}` : "No score"}</span>
        <span className="status-chip" data-level={risk.level}>
          {risk.status ? risk.status : t("ui.overview.status_not_given", "No level given")}
        </span>
      </button>
      {open ? (
        <div className="result-row-body">
          <div className="biomarker-detail">
            <dl className="biomarker-facts">
              {risk.percentile != null ? (
                <div>
                  <dt>{t("ui.overview.percentile", "Percentile")}</dt>
                  <dd>{risk.percentile}</dd>
                </div>
              ) : null}
              {risk.lifestyle_contribution != null ? (
                <div>
                  <dt>{t("ui.overview.lifestyle_share", "Lifestyle contribution")}</dt>
                  <dd>{risk.lifestyle_contribution}%</dd>
                </div>
              ) : null}
              {risk.previous_score != null ? (
                <div>
                  <dt>{t("ui.overview.previous", "Previous")}</dt>
                  <dd>
                    {risk.previous_score}
                    {risk.previous_on ? ` · ${shortDate(risk.previous_on)}` : ""}
                  </dd>
                </div>
              ) : null}
              {risk.measured_on ? (
                <div>
                  <dt>{t("ui.overview.assessed", "Assessed")}</dt>
                  <dd>{shortDate(risk.measured_on)}</dd>
                </div>
              ) : null}
            </dl>
            {(risk.contributing_factors ?? []).length > 0 ? (
              <p className="muted">
                {t("ui.overview.factors", "Contributing factors")}: {risk.contributing_factors!.join(", ")}
              </p>
            ) : null}
            {points.length >= 2 ? <TrendChart label={`${risk.name} risk score`} points={points} /> : null}
            <p className="muted">{t("ui.overview.not_a_diagnosis", "A predicted risk is not a diagnosis and not a measured result.")}</p>
            <AskCuraActions actions={riskAsks(risk, reportId)} onAsk={onAsk} label={`${t("ui.overview.ask_cura_about", "Ask CURA about")} ${risk.name}`} />
          </div>
        </div>
      ) : null}
    </li>
  );
}

function groupLine(group: RiskGroupSummary): string {
  const n = group.risk_count;
  const base = `${n} ${n === 1 ? "risk" : "risks"}`;
  return group.raised_count > 0 ? `${base} · ${group.raised_count} ${t("ui.overview.raised", "raised")}` : `${base} · ${t("ui.overview.none_raised", "none raised")}`;
}

/** Predicted risks the Bio-AI report returned. Never mixed with measured blood results. */
export function RiskOverviewView({ onAsk, onClose }: { onAsk: (text: string, contextRef: ContextRef) => void; onClose: () => void }) {
  const [reportId, setReportId] = useState<string | null>(null);
  const [openId, setOpenId] = useState<string | null>(null);
  const query = useRiskOverview(reportId);
  const data = query.data;
  const explainAll = () => onAsk(FULL_BIO_AI_ASK.text, { ...FULL_BIO_AI_ASK.contextRef, report_id: data?.report?.report_id ?? null });

  if (query.isLoading) {
    return (
      <section className="overview" aria-busy="true" aria-live="polite">
        <p className="muted">{t("ui.overview.loading_bio", "Opening your Bio-AI report…")}</p>
      </section>
    );
  }
  if (query.isError || !data) {
    return (
      <section className="overview" role="alert">
        <p>{t("ui.overview.bio_unavailable", "I couldn't open the visual overview just now.")}</p>
        <div className="chips">
          <button type="button" onClick={() => onAsk(FULL_BIO_AI_ASK.text, FULL_BIO_AI_ASK.contextRef)}>
            {t("ui.overview.explain_bio_in_chat", "Explain my Bio-AI report in chat")}
          </button>
          <button type="button" onClick={() => void query.refetch()}>
            {t("ui.overview.try_again", "Try again")}
          </button>
        </div>
      </section>
    );
  }

  const groups = data.groups ?? [];
  const open = groups.find((g) => g.id === openId) || null;
  const risks = data.risks ?? [];

  if (open) {
    const own = risks.filter((r) => r.group_id === open.id);
    return (
      <div className="overview">
        <section className="system-detail" aria-labelledby="risk-detail-title">
          <button type="button" className="overview-back" onClick={() => setOpenId(null)}>
            ← {t("ui.overview.all_risk_groups", "All risk areas")}
          </button>
          <h2 id="risk-detail-title" tabIndex={-1} ref={(el) => el?.focus()}>
            {open.name}
          </h2>
          <p className="muted">{groupLine(open)}</p>
          <p className="overview-note" role="note">
            {data.disclaimer}
          </p>
          <AskCuraActions actions={riskGroupAsks(open, own, data.report?.report_id)} onAsk={onAsk} label={`${t("ui.overview.ask_cura_about", "Ask CURA about")} ${open.name}`} />
          <ul className="result-list">
            {own.map((risk) => (
              <RiskRow key={risk.code} risk={risk} reportId={data.report?.report_id} onAsk={onAsk} />
            ))}
          </ul>
        </section>
      </div>
    );
  }

  return (
    <section className="overview" aria-labelledby="overview-title">
      <div className="overview-head">
        <div>
          <h2 id="overview-title">{t("ui.overview.bio_title", "Your Bio-AI report")}</h2>
          {data.report ? (
            <p className="muted">
              {t("ui.overview.report_dated", "Report dated")} {shortDate(data.report.report_date)}
              {data.report.metabolic_age != null ? ` · ${t("ui.overview.metabolic_age", "metabolic age")} ${data.report.metabolic_age}` : ""}
              {` · ${data.totals?.risk_count ?? 0} ${t("ui.overview.risks_assessed", "risks assessed")}`}
            </p>
          ) : null}
        </div>
        <button type="button" className="overview-close" onClick={onClose}>
          {t("ui.overview.close", "Close")}
        </button>
      </div>
      <p className="overview-note" role="note">
        {data.disclaimer}
      </p>
      {data.same_day_alternatives ? (
        <p className="muted">{t("ui.overview.same_day", "You have more than one Bio-AI report on this date. Choose which one to view.")}</p>
      ) : null}
      <ReportPicker reports={data.available_reports ?? []} selectedId={data.report?.report_id} onSelect={(id) => { setOpenId(null); setReportId(id); }} />
      {data.state !== "ready" || groups.length === 0 ? (
        <p>{t("ui.overview.no_risks", "This report has no risk results to show.")}</p>
      ) : (
        <ul className="system-grid" aria-label={t("ui.overview.risk_groups", "Risk areas in your report")}>
          {groups.map((group) => (
            <li key={group.id}>
              <button
                type="button"
                className="system-card"
                data-state={group.raised_count > 0 ? "attention" : "all_in_range"}
                aria-label={`${group.name}. ${groupLine(group)}. ${t("ui.overview.open_risks", "Open risks")}`}
                onClick={() => setOpenId(group.id)}
              >
                <span className="system-card-name">{group.name}</span>
                <span className="system-card-line">{groupLine(group)}</span>
                <span className="system-card-tag">{t("ui.overview.predicted_risk", "Predicted risk")}</span>
                {(group.key_findings ?? []).length > 0 ? (
                  <span className="system-card-findings">
                    {group.key_findings!.map((f) => (
                      <span key={f.code}>
                        {f.name}
                        {f.status ? ` · ${f.status}` : ""}
                      </span>
                    ))}
                  </span>
                ) : null}
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="chips">
        <button type="button" onClick={explainAll}>
          {t("ui.overview.explain_whole_bio", "Explain my whole Bio-AI report")}
        </button>
      </div>
    </section>
  );
}
