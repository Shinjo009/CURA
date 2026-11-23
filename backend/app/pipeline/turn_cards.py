"""Turns a finished answer into the card its turn kind calls for. One entry point for every card."""

from __future__ import annotations

import re

from app.contracts.followup import FollowUpSuggestion
from app.pipeline.turn_kinds import KindSpec


def attach_card(spec: KindSpec, *, answer: str, context, plan, presentation, suggestions):
    """Returns (answer, suggestions). Fills the matching field on the presentation when the answer follows its layout."""
    if spec.card == "risk_explanation":
        return _risk_explanation(answer, context, plan, presentation, suggestions)
    if spec.card == "nutrition_plan":
        return _nutrition_plan(answer, presentation, suggestions)
    return answer, suggestions


def _clear_cards(presentation) -> None:
    presentation.findings, presentation.raw_findings, presentation.themes = [], [], []
    presentation.headline = None


def _nutrition_plan(answer, presentation, suggestions):
    from app.pipeline.nutrition_plan import parse_nutrition_plan

    parsed = parse_nutrition_plan(answer)
    if parsed:
        # The cards carry the foods; the message keeps only the personal opening.
        answer, presentation.nutrition_plan = parsed
        _clear_cards(presentation)
    return answer, suggestions


def _risk_explanation(answer, context, plan, presentation, suggestions):
    from app.biomarkers.risk_overview import _display, _registry
    from app.pipeline.risk_explanation import parse_risk_explanation

    topic = (plan.topic or "").lower()
    risks = list(context.bio_ai_risks or [])
    risk = next((r for r in risks if (r.code or "").lower().replace(" ", "_") == topic), None) or (risks[0] if len(risks) == 1 else None)
    if risk is None:
        return answer, suggestions
    # The answer text stays whole for history. The cards read the same content from the structure.
    presentation.risk_explanation = parse_risk_explanation(answer, risk=risk, markers=list(context.markers or []))
    if not presentation.risk_explanation:
        return answer, suggestions
    _clear_cards(presentation)
    code = re.sub(r"[^a-z0-9]+", "_", (risk.code or risk.name or "").lower()).strip("_")
    name = _display(_registry(), code, risk.name).get("name", risk.name).lower()
    # Level 3 questions build on what was just explained.
    asks = [f"What causes {name}?", "Can my risk change over time?", f"Which foods can help lower my {name} risk?"]
    if presentation.risk_explanation.related_tests:
        asks.append("What do my blood tests say about this?")
    presentation.suggestion_chips = list(asks)
    return answer, [FollowUpSuggestion(text=t, category="explore", handling_path="CONTINUE_INTERPRETATION") for t in asks]
