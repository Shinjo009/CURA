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


SYSTEMS: tuple[BodySystem, ...] = (
    BodySystem("heart_circulation", "Heart & Circulation", 10),
    BodySystem("liver_health", "Liver Health", 20),
    BodySystem("kidney_urinary", "Kidney & Urinary", 30),
    BodySystem("blood_iron", "Blood & Iron", 40),
    BodySystem("blood_sugar_metabolism", "Blood Sugar & Metabolism", 50),
    BodySystem("vitamins_nutrition", "Vitamins & Nutrition", 60),
    BodySystem("thyroid_health", "Thyroid Health", 70),
    BodySystem("hormonal_health", "Hormonal Health", 80),
    BodySystem("bone_mineral", "Bone & Mineral Health", 90),
    BodySystem("immunity_inflammation", "Immunity & Inflammation", 100),
    BodySystem(
        "cancer_related",
        "Cancer-Related Markers",
        110,
        caveat="These markers are not a cancer screening test and are not an all clear on their own.",
    ),
    BodySystem(
        "sleep_recovery",
        "Sleep & Recovery",
        120,
        caveat="These results are related to recovery. They do not measure how well you sleep.",
        related_only=True,
    ),
)

OTHER_ID = "other_unmapped"
OTHER = BodySystem(OTHER_ID, "Other results", 900)
ALLERGY_ID = "allergy"
ALLERGY_NAME = "Allergy"

_BY_ID = {system.id: system for system in (*SYSTEMS, OTHER)}
_BY_NAME = {system.name.lower(): system for system in SYSTEMS}


def system_by_id(system_id: str) -> BodySystem | None:
    return _BY_ID.get(system_id)


def system_id_for_name(name: str) -> str | None:
    found = _BY_NAME.get((name or "").strip().lower())
    return found.id if found else None
