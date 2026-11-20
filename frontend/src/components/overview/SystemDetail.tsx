import { useEffect, useRef } from "react";
import type { ContextRef } from "../../types/chat";
import type { BiomarkerResult, SystemSummary } from "../../types/bodySystems";
import { orderResults, outsideRange, systemAsks, systemSummaryLine } from "../../lib/bodySystems";
import { AskCuraActions } from "./AskCuraActions";
import { ResultRow } from "./ResultRow";
import { StatusBreakdownBar } from "./StatusBreakdownBar";
import { t } from "../../i18n";

/** The results behind one card, plus results from other systems that are also relevant to it. */
export function SystemDetail({
  system,
  results,
  related,
  reportId,
  onAsk,
}: {
  system: SystemSummary;
  results: BiomarkerResult[];
  related: BiomarkerResult[];
  reportId?: string | null;
  onAsk: (text: string, contextRef: ContextRef) => void;
}) {
  const heading = useRef<HTMLHeadingElement>(null);
  useEffect(() => heading.current?.focus(), [system.id]);
  const own = system.scope === "related_only" ? related : results;
  const alsoRelated = system.scope === "related_only" ? [] : related;
  const partial = (system.group_coverage ?? []).filter((g) => g.partial);
  return (
    <section className="system-detail" aria-labelledby="system-detail-title">
      <h2 id="system-detail-title" tabIndex={-1} ref={heading}>
        {system.name}
      </h2>
      {system.about ? <p className="system-about">{system.about}</p> : null}
      <p className="muted">{systemSummaryLine(system)}</p>
      <StatusBreakdownBar counts={system.status_breakdown} name={system.name} />
      {system.caveat ? (
        <p className="overview-note" role="note">
          {system.caveat}
        </p>
      ) : null}
      {partial.length > 0 ? (
        <p className="muted">
          {t("ui.overview.partial", "Your report holds only some of the tests in")} {partial.map((g) => g.source_group).join(", ")}.{" "}
          {t("ui.overview.partial_tail", "Tests that are not on your report are not assessed.")}
        </p>
      ) : null}
      <AskCuraActions actions={systemAsks(system, own, reportId)} onAsk={onAsk} label={`${t("ui.overview.ask_cura_about", "Ask CURA about")} ${system.name}`} />
      <ul className="result-list">
        {orderResults(own).map((item, index) => (
          <ResultRow key={item.result_id} item={item} onAsk={onAsk} defaultOpen={index === 0 && outsideRange(system.status_breakdown) > 0 && own.length === 1} />
        ))}
      </ul>
      {alsoRelated.length > 0 ? (
        <>
          <h3>{t("ui.overview.also_relevant", "Also relevant here")}</h3>
          <p className="muted">{t("ui.overview.also_relevant_note", "These results are grouped under another system and are not counted again.")}</p>
          <ul className="result-list">
            {orderResults(alsoRelated).map((item) => (
              <ResultRow key={`rel-${item.result_id}`} item={item} onAsk={onAsk} />
            ))}
          </ul>
        </>
      ) : null}
    </section>
  );
}
