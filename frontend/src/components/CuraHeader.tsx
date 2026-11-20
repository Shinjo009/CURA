import { ThemeToggle } from "./ThemeToggle";
import { t } from "../i18n";

export function CuraHeader({
  onOpenSidebar,
  onBack,
}: {
  onOpenSidebar: () => void;
  /** Present when the member is one or more screens in. Steps back one screen. */
  onBack?: () => void;
}) {
  return (
    <header className="cura-header">
      <div className="title-row">
        {onBack ? (
          <button type="button" className="back-button" aria-label={t("ui.CuraHeader.back", "Back")} onClick={onBack}>
            <span aria-hidden="true">←</span> {t("ui.CuraHeader.back", "Back")}
          </button>
        ) : null}
        <button type="button" className="menu-button" aria-label={t("ui.CuraHeader.open_conversations", "Open conversations")} onClick={onOpenSidebar}>
          ☰
        </button>
        <h1>Cura ✨</h1>
        <span className="header-controls">
          <ThemeToggle />
        </span>
      </div>
    </header>
  );
}
