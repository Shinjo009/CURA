import type { StatusBreakdown } from "../../types/bodySystems";
import { breakdownSegments } from "../../lib/bodySystems";

/**
 * Proportions of a card's results by status. The legend spells every count out, so the bar is a
 * glance aid only and meaning never depends on colour.
 */
export function StatusBreakdownBar({ counts, name }: { counts: StatusBreakdown; name: string }) {
  const segments = breakdownSegments(counts);
  if (segments.length === 0) return null;
  const summary = `${name}: ${segments.map((s) => `${s.count} ${s.label.toLowerCase()}`).join(", ")}.`;
  return (
    <div className="sb">
      <div className="sb-bar" role="img" aria-label={summary}>
        {segments.map((s) => (
          <span key={s.key} className="sb-seg" data-status={s.key} style={{ flexGrow: s.count }} />
        ))}
      </div>
      <ul className="sb-legend" aria-hidden="true">
        {segments.map((s) => (
          <li key={s.key}>
            <span className="sb-key" data-status={s.key} /> {s.count} {s.label.toLowerCase()}
          </li>
        ))}
      </ul>
    </div>
  );
}
