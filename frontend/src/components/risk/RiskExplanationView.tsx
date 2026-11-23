import { useState, type ReactNode } from "react";
import type { RiskExplanationData } from "../../types/chat";
import { ValueCard } from "../messages/ValueCard";
import { t } from "../../i18n";

const ICONS: Record<string, string> = {
  meal: "🍽️",
  move: "🚶",
  sleep: "🌙",
  stress: "🧘",
  water: "💧",
  test: "🧪",
  doctor: "🩺",
  weight: "⚖️",
  smoke: "🚭",
  habit: "✅",
};

type Card = NonNullable<RiskExplanationData["score_card"]>;

/** One short paragraph per idea. Used for the condition and for what it means for the person. */
export function ExplainerSection({ title, paragraphs, id }: { title: string; paragraphs: string[]; id: string }) {
  return (
    <section className="risk-step" aria-labelledby={id}>
      <h3 id={id}>{title}</h3>
      {paragraphs.map((p) => (
        <p key={p}>{p}</p>
      ))}
    </section>
  );
}

/** Verified values from the report: score out of 100, the report's own level and date. Nothing here is model written. */
export function RiskScoreCard({ card }: { card: Card }) {
  const [open, setOpen] = useState(false);
  const score = card.score;
  const pct = typeof score === "number" ? Math.min(Math.max(score, 0), 100) : null;
  const details: Array<[string, ReactNode]> = [];
  if (card.percentile != null) details.push([t("ui.risk.percentile", "Percentile"), card.percentile]);
  if (card.lifestyle_contribution != null) details.push([t("ui.risk.lifestyle", "Lifestyle contribution"), `${card.lifestyle_contribution}%`]);
  if (card.previous_score != null) details.push([t("ui.risk.previous", "Previous score"), card.previous_score]);
  const factors = card.contributing_factors ?? [];
  const hasDetails = details.length > 0 || factors.length > 0;
  return (
    <article className="risk-score-card" data-level={card.level} data-testid="risk-score-card">
      <header>
        <span className="muted">{`${card.name} ${t("ui.risk.risk_score", "risk score")}`}</span>
        {card.status ? <span className="risk-level" data-level={card.level}>{card.status}</span> : null}
      </header>
      {pct != null ? (
        <>
          <p className="risk-score-value">
            <strong>{score}</strong>
            <span> / 100</span>
          </p>
          <div className="risk-meter" role="img" aria-label={`${card.name} score ${score} out of 100`}>
            <span style={{ width: `${pct}%` }} />
          </div>
          <div className="risk-meter-ends" aria-hidden="true">
            <span>0</span>
            <span>100</span>
          </div>
        </>
      ) : (
        <p className="muted">{t("ui.risk.no_score", "No score in this report.")}</p>
      )}
      {card.assessed_on ? <p className="muted">{`${t("ui.risk.assessed_on", "Assessed on")} ${longDate(card.assessed_on)}`}</p> : null}
      {hasDetails ? (
        <>
          <button type="button" className="expand-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
            {t("ui.risk.view_details", "View assessment details")}
            <span aria-hidden="true">{open ? "⌃" : "⌄"}</span>
          </button>
          {open ? (
            <div className="risk-details">
              <dl className="biomarker-facts">
                {details.map(([k, v]) => (
                  <div key={k}>
                    <dt>{k}</dt>
                    <dd>{v}</dd>
                  </div>
                ))}
              </dl>
              {factors.length > 0 ? (
                <p className="muted">
                  {t("ui.risk.from_report", "Contributing factors in your report")}: {factors.join(", ")}
                </p>
              ) : null}
            </div>
          ) : null}
        </>
      ) : null}
    </article>
  );
}

export function RelatedBiomarkers({ tests }: { tests: RiskExplanationData["related_tests"] }) {
  if (tests.length === 0) return null;
  return (
    <section className="risk-step" aria-labelledby="risk-related">
      <h3 id="risk-related">{t("ui.risk.related_tests", "Your related blood tests")}</h3>
      <div className="value-cards">
        {tests.map((item) => (
          <ValueCard key={item.finding.label} finding={item.finding} note={item.why} />
        ))}
      </div>
    </section>
  );
}

export function ActionCards({ actions, title }: { actions: RiskExplanationData["actions"]; title: string }) {
  if (actions.length === 0) return null;
  return (
    <section className="risk-step" aria-labelledby="risk-actions">
      <h3 id="risk-actions">{title}</h3>
      <ul className="action-cards">
        {actions.map((action) => (
          <li key={action.title} className="action-card" data-testid="action-card">
            <span className="action-icon" aria-hidden="true">
              {ICONS[action.icon] ?? ICONS.habit}
            </span>
            <div>
              <strong>{action.title}</strong>
              {action.detail ? <p>{action.detail}</p> : null}
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

/** Extra reading (signs, causes, tests, prevention) stays closed until the person wants it. */
export function ExpandableInfo({ sections, generalNote }: { sections: RiskExplanationData["more"]; generalNote?: string }) {
  if (sections.length === 0) return null;
  return (
    <section className="risk-more" aria-label={t("ui.risk.more", "More to explore")}>
      {sections.map((section) => (
        <details key={section.title} className="risk-expand">
          <summary>{section.title}</summary>
          {generalNote && /raise|cause|factor/i.test(section.title) ? <p className="muted">{generalNote}</p> : null}
          <ul>
            {section.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </details>
      ))}
    </section>
  );
}

function longDate(value: string): string {
  const d = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

/** The four steps: what it is, what the report says, what it means for me, what I can do. */
export function RiskExplanationView({ data }: { data: RiskExplanationData }) {
  return (
    <div className="risk-explanation" data-testid="risk-explanation">
      <ExplainerSection id="risk-what" title={data.condition_title} paragraphs={data.condition} />
      {data.score_card ? (
        <section className="risk-step" aria-labelledby="risk-report">
          <h3 id="risk-report">{t("ui.risk.what_report_says", "What does your health report say?")}</h3>
          <RiskScoreCard card={data.score_card} />
        </section>
      ) : null}
      <ExplainerSection id="risk-meaning" title={data.meaning_title} paragraphs={data.meaning} />
      <RelatedBiomarkers tests={data.related_tests} />
      <ActionCards actions={data.actions} title={t("ui.risk.protect", "How can you protect your future health?")} />
      <ExpandableInfo sections={data.more} generalNote={t("ui.risk.general_note", "General information, not confirmed for you.")} />
    </div>
  );
}
