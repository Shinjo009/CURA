import { useState } from "react";
import type { RiskExplanationData } from "../../types/chat";
import { ValueCard } from "../messages/ValueCard";
import { t } from "../../i18n";

const ICON_PATHS: Record<string, string> = {
  meal: "M7 3v8M4 3v5a3 3 0 0 0 3 3M10 3v5a3 3 0 0 1-3 3M7 11v10M17 3c-2 2-3 5-3 8h3v10",
  move: "M8 4c-1.5 0-2.5 1.5-2.5 3.5S6.5 11 8 11s2.5-1 2.5-3.5S9.5 4 8 4zM6.5 14h3l.5 3a1.5 1.5 0 0 1-3 0zM16 8c-1.5 0-2.5 1.5-2.5 3.5S14.5 15 16 15s2.5-1 2.5-3.5S17.5 8 16 8zM14.5 18h3l.5 2a1.5 1.5 0 0 1-3 0z",
  sleep: "M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z",
  stress: "M12 21c-4-3-7-6-7-10a4 4 0 0 1 7-2 4 4 0 0 1 7 2c0 4-3 7-7 10z",
  water: "M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11z",
  test: "M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3M8 15h8",
  doctor: "M6 3v6a4 4 0 0 0 8 0V3M10 13v3a4 4 0 0 0 8 0v-2M18 12a2 2 0 1 0 0 4 2 2 0 0 0 0-4z",
  weight: "M5 8h14l1 12H4zM9 8a3 3 0 0 1 6 0M12 12v3",
  smoke: "M4 16h13v3H4zM19 16v3M17 8c0-2 2-2 2-4M13 8c0-2 2-2 2-4",
  habit: "M5 12l4 4 10-10",
};

/** A simple line icon. Decorative: the action title carries the meaning. */
export function LineIcon({ name }: { name: string }) {
  return (
    <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d={ICON_PATHS[name] ?? ICON_PATHS.habit} />
    </svg>
  );
}

type Card = NonNullable<RiskExplanationData["score_card"]>;

/** One short paragraph per idea. Used for the condition and for what it means for the person. */
export function ExplainerSection({ title, paragraphs, id }: { title: string; paragraphs: string[]; id: string }) {
  return (
    <section className="risk-step" aria-labelledby={id}>
      <h3 id={id}>{title}</h3>
      <div className="risk-points">
        {paragraphs.map((p) => (
          <p key={p}>{p}</p>
        ))}
      </div>
    </section>
  );
}

/** Verified values from the report: score out of 100, the report's own level and date. Nothing here is model written. */
export function RiskScoreCard({ card }: { card: Card }) {
  const score = card.score;
  const pct = typeof score === "number" ? Math.min(Math.max(score, 0), 100) : null;
  return (
    <article className="risk-score-card" data-level={card.level} data-testid="risk-score-card">
      <header>
        <span className="muted">{`${card.name} ${t("ui.risk.risk_score", "risk score")}`}</span>
        {card.status ? (
          <span className="risk-level" data-level={card.level}>
            <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              {card.level === "raised" ? <path d="M12 8v5M12 16.5v.5M12 3l9.5 17h-19z" /> : <path d="M8 12.5l3 3 5-6M12 3a9 9 0 1 0 0 18 9 9 0 0 0 0-18z" />}
            </svg>
            {card.status}
          </span>
        ) : null}
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
      <p className="risk-card-note">{t("ui.risk.card_note", "This card is an estimate of future risk, not a diagnosis and not a percent chance.")}</p>
    </article>
  );
}

/** Invites the person to look at their own related results. Names and values come from the report. */
export function RelatedBiomarkers({ tests, riskName, onAsk, title, text, button }: { tests: RiskExplanationData["related_tests"]; riskName: string; onAsk?: (text: string) => void; title?: string; text?: string; button?: string }) {
  if (tests.length === 0) return null;
  const names = tests.map((item) => item.finding.label);
  const list = names.length > 1 ? `${names.slice(0, -1).join(", ")} and ${names[names.length - 1]}` : names[0];
  return (
    <section className="related-card" aria-labelledby="risk-related" data-testid="related-tests">
      <h3 id="risk-related">
        <span className="related-icon"><LineIcon name="test" /></span>
        {title || t("ui.risk.want_to_know", "Want to see your related blood tests?")}
      </h3>
      <p>{text || `${t("ui.risk.your_tests", "Your")} ${list} ${t("ui.risk.help_understand", "can help us understand this.")}`}</p>
      <ul className="related-values">
        {tests.map((item) => (
          <li key={item.finding.label}>
            <span>{item.finding.label}</span>
            <strong>{`${item.finding.value ?? ""}${item.finding.unit ? ` ${item.finding.unit}` : ""}`}</strong>
          </li>
        ))}
      </ul>
      {onAsk ? (
        <button type="button" className="outline-button" onClick={() => onAsk(`What do my ${list} results say about my ${riskName} risk?`)}>
          {button || t("ui.risk.check_results", "Check my blood test results")}
        </button>
      ) : null}
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
            <span className="action-icon">
              <LineIcon name={action.icon} />
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

/** Extra reading (signs, causes, tests, prevention) stays closed until the person opens it. */
function ExpandItem({ section, note }: { section: RiskExplanationData["more"][number]; note?: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="risk-expand" data-open={open}>
      <button type="button" className="expand-toggle" aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <strong>{section.title}</strong>
        <span aria-hidden="true">{open ? "⌃" : "⌄"}</span>
      </button>
      {open ? (
        <>
          {note ? <p className="muted">{note}</p> : null}
          <ul>
            {section.items.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        </>
      ) : null}
    </div>
  );
}

export function ExpandableInfo({ sections, generalNote }: { sections: RiskExplanationData["more"]; generalNote?: string }) {
  if (sections.length === 0) return null;
  return (
    <section className="risk-more" aria-label={t("ui.risk.more", "More to explore")}>
      {sections.map((section) => (
        <ExpandItem key={section.title} section={section} note={generalNote && /raise|cause|factor/i.test(section.title) ? generalNote : undefined} />
      ))}
    </section>
  );
}

function longDate(value: string): string {
  const d = new Date(`${value.slice(0, 10)}T00:00:00`);
  return Number.isNaN(d.getTime()) ? value : d.toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" });
}

/** The four steps: what it is, what the report says, what it means for me, what I can do. */
export function RiskExplanationView({ data, onAsk }: { data: RiskExplanationData; onAsk?: (text: string) => void }) {
  const name = data.score_card?.name ?? "";
  return (
    <div className="risk-explanation" data-testid="risk-explanation">
      {name ? (
        <p className="risk-opening">{`${t("ui.risk.lets_understand", "Let's understand what")} ${name} ${t("ui.risk.is_and_means", "is and what your result means for your health.")}`}</p>
      ) : null}
      <ExplainerSection id="risk-what" title={data.condition_title} paragraphs={data.condition} />
      <hr className="risk-divider" />
      {data.score_card ? (
        <section className="risk-step" aria-labelledby="risk-report">
          <h3 id="risk-report">{t("ui.risk.what_report_says", "What does your health report say?")}</h3>
          <RiskScoreCard card={data.score_card} />
        </section>
      ) : null}
      <ExplainerSection id="risk-meaning" title={data.meaning_title} paragraphs={data.meaning} />
      <RelatedBiomarkers tests={data.related_tests} riskName={name} onAsk={onAsk} title={data.related_title} text={data.related_text} button={data.related_button} />
      <hr className="risk-divider" />
      <ActionCards actions={data.actions} title={t("ui.risk.protect", "How can you protect your future health?")} />
      <ExpandableInfo sections={data.more} generalNote={t("ui.risk.general_note", "General information, not confirmed for you.")} />
    </div>
  );
}
