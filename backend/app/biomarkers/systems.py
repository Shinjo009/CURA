"""Body-system definitions for the overview. Display categories only, not clinical classifications."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BodySystem:
    id: str
    name: str
    order: int
    # Shown on the card and in the detail view when the system has results.
    caveat: str | None = None
    # A system with no primary biomarkers: it appears only through cross references.
    related_only: bool = False
    # One plain sentence on what the system covers, shown on its card.
    about: str = ""


SYSTEMS: tuple[BodySystem, ...] = (
    BodySystem("heart_circulation", "Heart & Circulation", 10, about="How your body handles the cholesterol and fats that affect your heart and blood vessels."),
    BodySystem("liver_health", "Liver Health", 20, about="How well your liver is working to process food, medicines and waste."),
    BodySystem("kidney_urinary", "Kidney & Urinary", 30, about="How well your kidneys filter waste and keep your salts and fluids in balance."),
    BodySystem("blood_iron", "Blood & Iron", 40, about="Your blood cells and iron, which carry oxygen around your body."),
    BodySystem("blood_sugar_metabolism", "Blood Sugar & Metabolism", 50, about="How your body handles sugar and turns food into energy."),
    BodySystem("vitamins_nutrition", "Vitamins & Nutrition", 60, about="The vitamins and minerals your body needs to run well."),
    BodySystem("thyroid_health", "Thyroid Health", 70, about="The thyroid hormones that set your energy level and metabolism."),
    BodySystem("hormonal_health", "Hormonal Health", 80, about="Hormones that shape your energy, stress, growth and reproductive health."),
    BodySystem("bone_mineral", "Bone & Mineral Health", 90, about="Minerals that keep your bones and muscles strong."),
    BodySystem("immunity_inflammation", "Immunity & Inflammation", 100, about="Signs of inflammation and how your body fights infection."),
    BodySystem(
        "cancer_related",
        "Cancer-Related Markers",
        110, about="Markers doctors may use alongside other tests. On their own they are not a screening.",
        caveat="These markers are not a cancer screening test and are not an all clear on their own.",
    ),
    BodySystem(
        "sleep_recovery",
        "Sleep & Recovery",
        120, about="Results linked to stress and recovery, such as cortisol, magnesium and zinc.",
        caveat="These results are related to recovery. They do not measure how well you sleep.",
        related_only=True,
    ),
)

OTHER_ID = "other_unmapped"
OTHER = BodySystem(OTHER_ID, "Other results", 900, about="Results that have not been grouped into a body system yet.")
ALLERGY_ID = "allergy"
ALLERGY_NAME = "Allergy"
ALLERGY_ABOUT = "Antibody tests for things your body may react to, such as foods, pollen and dust."

_BY_ID = {system.id: system for system in (*SYSTEMS, OTHER)}
_BY_NAME = {system.name.lower(): system for system in SYSTEMS}


def system_by_id(system_id: str) -> BodySystem | None:
    return _BY_ID.get(system_id)


def system_id_for_name(name: str) -> str | None:
    found = _BY_NAME.get((name or "").strip().lower())
    return found.id if found else None
