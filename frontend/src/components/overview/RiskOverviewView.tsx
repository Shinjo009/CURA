import { useState } from "react";
import type { ContextRef } from "../../types/chat";
import type { RiskGroupSummary, RiskResult } from "../../types/bodySystems";
import { useRiskOverview } from "../../hooks/useReportOverviews";
import { FULL_BIO_AI_ASK, reportLevelAsks, riskAsks, riskGroupAsks, riskName } from "../../lib/bodySystems";
import { shortDate, TrendChart } from "../marker/TrendChart";
import { AskCuraActions } from "./AskCuraActions";
import { ReportPicker } from "./ReportPicker";
import { t } from "../../i18n";

/** Medical name or a one sentence explanation: the secondary line under an everyday name. */
function secondaryLine(risk: RiskResult): string {
  return risk.medical_name || risk.explain || "";
}

function RiskRow({ risk, reportId, onAsk }: { risk: RiskResult; reportId?: string | null; onAsk: (text: string, ref: ContextRef) => void }) {
  const [open, setOpen] = useState(false);
  const points = (risk.history ?? []).filter((p) => typeof p.score === "number").map((p) => ({ date: p.date, value: p.score as number, status: p.status ?? undefined }));
  return (
    <li className="result-row" data-level={risk.level}>
      <button type="button" className="result-row-head" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <span className="result-row-name">
          {riskName(risk)}
          <span className="result-row-group">{secondaryLine(risk) || t("ui.overview.predicted_risk", "Predicted risk")}</span>
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
            {points.length >= 2 ? <TrendChart label={`${riskName(risk)} risk score`} points={points} /> : null}
            <p className="muted">{t("ui.overview.not_a_diagnosis", "A predicted risk is not a diagnosis and not a measured result.")}</p>
            <AskCuraActions actions={riskAsks(risk, reportId)} onAsk={onAsk} label={`${t("ui.overview.ask_cura_about", "Ask CURA about")} ${riskName(risk)}`} />
          </div>
        </div>
      ) : null}
    </li>
  );
}

function groupLine(group: RiskGroupSummary): string {
  const n = group.risk_count;
  const base = `${n} ${n === 1 ? "risk" : "risks"}`;
  if (group.raised_count === 0) return `${base} · ${t("ui.overview.none_raised_cap", "None raised")}`;
  return `${base} · ${group.raised_count} ${t("ui.overview.raised", "raised")}`;
}

function longDate(value: string): string {
  const d = new Date(value);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

/** Ring split into raised and not raised. The numbers beside it say the same thing in words. */
function RiskDonut({ total, raised }: { total: number; raised: number }) {
  const r = 46;
  const c = 2 * Math.PI * r;
  const share = total > 0 ? raised / total : 0;
  return (
    <div className="risk-donut" role="img" aria-label={`${total} risks assessed, ${raised} needs attention`}>
      <svg viewBox="0 0 120 120" width="120" height="120" aria-hidden="true">
        <circle cx="60" cy="60" r={r} fill="none" strokeWidth="12" className="donut-clear" />
        {raised > 0 ? (
          <circle
            cx="60"
            cy="60"
            r={r}
            fill="none"
            strokeWidth="12"
            className="donut-raised"
            strokeDasharray={`${c * share} ${c}`}
            transform="rotate(-90 60 60)"
          />
        ) : null}
      </svg>
      <div className="donut-centre">
        <strong>{total}</strong>
        <span>{t("ui.overview.risks_assessed_label", "Risks assessed")}</span>
      </div>
    </div>
  );
}

/** Predicted risks the Bio-AI report returned. Never mixed with measured blood results. */
export function RiskOverviewView({
  onAsk,
  openId,
  onOpenChange,
}: {
  onAsk: (text: string, contextRef: ContextRef) => void;
  openId: string | null;
  onOpenChange: (id: string | null) => void;
}) {
  const [reportId, setReportId] = useState<string | null>(null);
  const setOpenId = onOpenChange;
  const query = useRiskOverview(reportId);
  const data = query.data;

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
          <h2 id="risk-detail-title" tabIndex={-1} ref={(el) => el?.focus()}>
            {open.name}
          </h2>
          {open.about ? <p className="system-about">{open.about}</p> : null}
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

  const total = data.totals?.risk_count ?? risks.length;
  const raisedRisks = risks.filter((r) => r.level === "raised");
  const raisedCount = raisedRisks.length;
  const clearCount = Math.max(total - raisedCount, 0);
  const age = data.report?.metabolic_age;
  const reportRef: ContextRef = { type: "bio_ai_report", source: "supershyft", report_id: data.report?.report_id ?? null };
  const openGroupOf = (risk: RiskResult) => groups.find((g) => g.id === risk.group_id)?.id ?? null;

  return (
    <section className="overview bio-overview" aria-labelledby="overview-title">
      <h2 id="overview-title">{t("ui.overview.bio_title", "Understand your future health")}</h2>
      {data.report ? (
        <p className="muted">
          {t("ui.overview.bio_assessment", "Bio-AI assessment")} · {longDate(data.report.report_date)}
        </p>
      ) : null}
      <p className="bio-intro">
        {t("ui.overview.bio_intro", "Your Bio-AI report helps you understand which health conditions you may be more likely to develop in the future, based on your blood results and lifestyle.")}
      </p>
      {data.same_day_alternatives ? (
        <p className="muted">{t("ui.overview.same_day", "You have more than one Bio-AI report on this date. Choose which one to view.")}</p>
      ) : null}
      <ReportPicker reports={data.available_reports ?? []} selectedId={data.report?.report_id} onSelect={(id) => { setOpenId(null); setReportId(id); }} />
      {data.state !== "ready" || groups.length === 0 ? (
        <p>{t("ui.overview.no_risks", "This report has no risk results to show.")}</p>
      ) : (
        <>
          <div className="risk-summary" data-testid="risk-summary">
            <RiskDonut total={total} raised={raisedCount} />
            <ul className="risk-legend">
              <li data-kind="clear">
                <span className="legend-dot" aria-hidden="true" />
                <strong>{clearCount}</strong>
                <span>{t("ui.overview.no_raised_risk", "No raised risk")}</span>
              </li>
              <li data-kind="raised">
                <span className="legend-dot" aria-hidden="true" />
                <strong>{raisedCount}</strong>
                <span>{t("ui.overview.needs_attention", "Needs attention")}</span>
              </li>
            </ul>
          </div>
          {age != null ? (
            <section className="metabolic-age" aria-labelledby="metabolic-age-title">
              <p id="metabolic-age-title" className="muted">{t("ui.overview.your_metabolic_age", "Your metabolic age")}</p>
              <p className="metabolic-age-value">{`${Math.round(age)} ${t("ui.overview.years", "years")}`}</p>
              <p>{t("ui.overview.metabolic_age_about", "An estimate of your metabolic health expressed as an age.")}</p>
              <button type="button" className="link-button" onClick={() => onAsk("What does my metabolic age mean for my health?", reportRef)}>
                {t("ui.overview.understand_metabolic_age", "Understand my metabolic age")}
              </button>
            </section>
          ) : null}
          <section className="attention-section" aria-labelledby="attention-title">
            <h3 id="attention-title">{t("ui.overview.what_deserves_attention", "What deserves your attention")}</h3>
            {raisedRisks.length === 0 ? (
              <p className="muted">{t("ui.overview.nothing_raised", "No risk is raised in this report.")}</p>
            ) : (
              <ul className="attention-list">
                {raisedRisks.map((risk) => (
                  <li key={risk.code} className="attention-card" data-testid="attention-card">
                    <strong>{riskName(risk)}</strong>
                    {secondaryLine(risk) ? <span className="muted">{secondaryLine(risk)}</span> : null}
                    <span className="attention-level">{risk.status ? `${risk.status} ${t("ui.overview.predicted_risk_lower", "predicted risk")}` : t("ui.overview.raised_risk", "Raised predicted risk")}</span>
                    {risk.about ? <p>{`${t("ui.overview.suggests", "Your assessment suggests a higher risk of")} ${risk.about}.`}</p> : null}
                    <button type="button" className="outline-button" onClick={() => onAsk(riskAsks(risk, data.report?.report_id)[0].text, riskAsks(risk, data.report?.report_id)[0].contextRef)}>
                      {t("ui.overview.understand_this_risk", "Understand this risk")}
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <p className="overview-note" role="note">
              {data.disclaimer}
            </p>
          </section>
          <section className="explore-section" aria-labelledby="explore-title">
            <h3 id="explore-title">{t("ui.overview.explore_health", "Explore your health")}</h3>
            <p className="muted">{t("ui.overview.explore_sub", "Understand different areas of your body")}</p>
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
                    {group.about ? <span className="system-card-about">{group.about}</span> : null}
                    <span className="system-card-line">{groupLine(group)}</span>
                    <span className="system-card-tag">{t("ui.overview.explore_risks", "Explore health risks")} →</span>
                  </button>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
      <AskCuraActions actions={reportLevelAsks(data.report?.report_id)} onAsk={onAsk} label={t("ui.overview.ask_about_report", "Ask CURA about your report")} />
    </section>
  );
}
