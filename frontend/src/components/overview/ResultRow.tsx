import { useId, useState } from "react";
import type { ContextRef } from "../../types/chat";
import type { BiomarkerResult } from "../../types/bodySystems";
import { statusDisplay } from "../../lib/bodySystems";
import { fmt } from "../../lib/range";
import { BiomarkerDetail } from "./BiomarkerDetail";

/** One result as a disclosure row: name, value and status at a glance, the full detail on demand. */
export function ResultRow({
  item,
  onAsk,
  defaultOpen = false,
}: {
  item: BiomarkerResult;
  onAsk: (text: string, contextRef: ContextRef) => void;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const panelId = useId();
  const status = statusDisplay(item.status);
  const value = item.value == null ? "No result" : `${fmt(item.value)}${item.unit ? ` ${item.unit}` : ""}`;
  return (
    <li className="result-row" data-status={item.status}>
      <button type="button" className="result-row-head" aria-expanded={open} aria-controls={panelId} onClick={() => setOpen((v) => !v)}>
        <span className="result-row-name">
          {item.display_name}
          {item.source_group ? <span className="result-row-group">{item.source_group}</span> : null}
        </span>
        <span className="result-row-value">{value}</span>
        <span className="status-chip" data-status={item.status}>
          <span aria-hidden="true">{status.icon}</span> {status.label}
        </span>
      </button>
      {open ? (
        <div id={panelId} className="result-row-body">
          <BiomarkerDetail item={item} onAsk={onAsk} />
        </div>
      ) : null}
    </li>
  );
}
