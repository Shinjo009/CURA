"""Resolve one report result to a canonical biomarker and body system.

Order, most exact first: allergy source group, source label (with the source group to break ties),
alias, label slug, CURA key, then the existing lab-parameter resolver. A result that nothing
recognises is kept and filed under Other / Unmapped Results with a review flag. A result is never
dropped and never guessed into a system.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.biomarkers.registry import AllergyGroup, Registry, load_registry, normalize_label
from app.biomarkers.systems import ALLERGY_ID, OTHER_ID


@dataclass(frozen=True)
class Resolution:
    canonical_id: str | None
    method: str
    primary_system: str
    secondary_systems: tuple[str, ...] = ()
    derived: bool = False
    review_note: str | None = None
    allergy_subsection: str | None = None

    @property
    def needs_mapping_review(self) -> bool:
        return self.canonical_id is None and self.primary_system != ALLERGY_ID


def _found(reg: Registry, canonical: str, method: str, note: str | None = None) -> Resolution:
    entry = reg.entries[canonical]
    return Resolution(
        canonical_id=canonical,
        method=method,
        primary_system=entry.primary_system,
        secondary_systems=entry.secondary_systems,
        derived=entry.derived,
        review_note=note or entry.review_note,
    )


def _allergy(reg: Registry, label: str, group_n: str) -> AllergyGroup | None:
    for item in reg.allergy_groups:
        name = normalize_label(item.group, reg.spelling)
        if group_n == name or (not group_n and label == name):
            return item
    return None


def resolve_marker(name: str, key: str | None = None, group: str | None = None) -> Resolution:
    reg = load_registry()
    label = normalize_label(name, reg.spelling)
    group_n = normalize_label(group or "", reg.spelling)
    key = (key or "").strip().lower()

    allergy = _allergy(reg, label, group_n)
    if allergy is not None:
        return Resolution(None, "allergy_group", ALLERGY_ID, allergy_subsection=allergy.subsection)

    candidates = reg.by_label.get(label, ())
    ids = list(dict.fromkeys(canonical for canonical, _ in candidates))
    if len(ids) > 1:
        in_group = list(dict.fromkeys(c for c, g in candidates if g == group_n))
        ids = in_group if len(in_group) == 1 else []
    if len(ids) == 1:
        canonical = ids[0]
        urine_only = canonical.startswith("urine_")
        blocked = urine_only and label in reg.ambiguous_bare and "urine" not in group_n and not key.startswith("urine")
        if not blocked:
            exact_group = any(c == canonical and g == group_n for c, g in candidates)
            return _found(reg, canonical, "source_group_label" if exact_group else "source_label")

    alias = reg.by_alias.get(label)
    if alias:
        return _found(reg, alias, "alias")

    slug = label.replace(" ", "_")
    if slug in reg.entries:
        return _found(reg, slug, "slug")

    if key in reg.key_bridge:
        return _found(reg, reg.key_bridge[key], "cura_key", reg.bridge_notes.get(key))

    from app.pipeline.lab_parameters import resolve_biomarker

    match = resolve_biomarker(name)
    if match and match.canonical_code in reg.key_bridge:
        canonical = reg.key_bridge[match.canonical_code]
        return _found(reg, canonical, "lab_parameter", reg.bridge_notes.get(match.canonical_code))

    return Resolution(None, "unmapped", OTHER_ID)
