"""One place that says what each kind of turn needs.

A turn is resolved to a kind once, from the explicit entry point a card sends or, for typed text,
from the message. Everything that used to branch on the entry point, a message pattern or an
"explainer" flag reads this registry instead: what data to load, which prompt module to add,
whether the answer keeps its section layout, and which card the answer becomes.

Adding a kind is adding one row here, one prompt module and (for a card) one parser.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TurnKind(str, Enum):
    general = "general"
    bio_ai_risk = "bio_ai_risk"  # Understand this risk: four step explanation of one Bio-AI risk
    health_area = "health_area"  # report or health area question: blood, Bio-AI and habits together
    nutrition_overview = "nutrition_overview"  # the Nutrition card


@dataclass(frozen=True)
class KindSpec:
    needs_blood: bool = False
    needs_bio_ai: bool = False
    needs_questionnaire: bool = False
    # The model sees the whole panel and every risk; relevance is decided in the prompt, not in retrieval.
    whole_record: bool = False
    # Name of the prompt add-on in prompt_modules (looked up by name there).
    prompt_module: str | None = None
    # Headings and bullets stay as written so the answer can be read back by section.
    keep_layout: bool = False
    # Which card the answer is turned into ("risk_explanation", "nutrition_plan") or None.
    card: str | None = None
    # No "X was not found" notes: the model was given everything.
    skip_coverage_notes: bool = False


REGISTRY: dict[TurnKind, KindSpec] = {
    TurnKind.general: KindSpec(),
    TurnKind.bio_ai_risk: KindSpec(
        needs_blood=True, needs_bio_ai=True, needs_questionnaire=True, whole_record=True,
        prompt_module="RISK_EXPLAINER", keep_layout=True, card="risk_explanation", skip_coverage_notes=True,
    ),
    TurnKind.health_area: KindSpec(
        needs_blood=True, needs_bio_ai=True, needs_questionnaire=True, whole_record=True,
        prompt_module="HEALTH_AREA", skip_coverage_notes=True,
    ),
    TurnKind.nutrition_overview: KindSpec(prompt_module="NUTRITION_OVERVIEW", keep_layout=True, card="nutrition_plan"),
}

# The entry points a card can send, and the kind each one means.
ENTRY_POINT_KINDS = {"risk_explainer": TurnKind.bio_ai_risk, "health_area": TurnKind.health_area}


def resolve_turn_kind(message: str | None, entry_point: str | None = None) -> TurnKind:
    """An explicit entry point wins. Typed text is matched only for the Nutrition overview."""
    if entry_point in ENTRY_POINT_KINDS:
        return ENTRY_POINT_KINDS[entry_point]
    from app.pipeline.prompt_modules import is_nutrition_overview

    return TurnKind.nutrition_overview if is_nutrition_overview(message or "") else TurnKind.general


def kind_of(context, message: str | None = None) -> TurnKind:
    """The kind recorded on the context, or, for a context built without one, the kind the message means."""
    recorded = getattr(context, "turn_kind", None)
    if recorded and recorded != TurnKind.general.value:
        return TurnKind(recorded)
    return resolve_turn_kind(message, None)


def spec_for(kind: TurnKind | str | None) -> KindSpec:
    try:
        return REGISTRY[TurnKind(kind or "general")]
    except ValueError:
        return REGISTRY[TurnKind.general]
