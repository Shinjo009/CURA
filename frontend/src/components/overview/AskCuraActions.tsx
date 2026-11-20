import type { ContextRef } from "../../types/chat";
import type { AskAction } from "../../lib/bodySystems";
import { t } from "../../i18n";

/** Questions that carry the opened result as context, so CURA answers about exactly this. */
export function AskCuraActions({
  actions,
  onAsk,
  label,
}: {
  actions: AskAction[];
  onAsk: (text: string, contextRef: ContextRef) => void;
  label?: string;
}) {
  if (actions.length === 0) return null;
  return (
    <div className="chips overview-ask" role="group" aria-label={label || t("ui.overview.ask_cura", "Ask CURA")}>
      {actions.map((action) => (
        <button key={action.id} type="button" onClick={() => onAsk(action.text, action.contextRef)}>
          {action.label}
        </button>
      ))}
    </div>
  );
}
