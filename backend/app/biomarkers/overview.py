"""Build the body-system overview from the member's own blood reports. No model call.

Everything here is derived from the structured report: names, values, units, reference ranges,
flags and dates are passed through, and nothing is recomputed that the report already states.
Only results present in the selected report produce output, so a system the member has no results
for never appears and a missing test is never shown as normal.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field

from app.biomarkers.registry import load_registry, normalize_label
from app.biomarkers.resolver import Resolution, resolve_marker
from app.biomarkers.systems import (
    ALLERGY_ABOUT,
    ALLERGY_ID,
    ALLERGY_NAME,
    OTHER,
    OTHER_ID,
    SYSTEMS,
    BodySystem,
)
from app.contracts.blood import BloodMarker, BloodReport
from app.contracts.body_systems import (
    AllergySubsection,
    BiomarkerResult,
    BodySystemOverview,
    GroupCoverage,
    HistoryPoint,
    KeyFinding,
    ReportRef,
    ReportTotals,
    StatusBreakdown,
    SystemSummary,
)
from app.pipeline.gap_words import how_far
from app.pipeline.health_overview import _trend

logger = logging.getLogger(__name__)

_ABNORMAL = {"low", "high", "critical"}
_SEVERITY = {"critical": 0, "high": 1, "low": 1}


class ReportNotFound(LookupError):
    """The requested report id is not one of this member's reports."""


@dataclass
class _Record:
    marker: BloodMarker
    index: int
    resolution: Resolution
    result_id: str
    status: str
    status_source: str
    identity: tuple
    group_n: str
    unit_n: str
    duplicates: int = 0
    conflicts: list[float] = field(default_factory=list)


def _day(value) -> str | None:
    return str(value)[:10] if value else None


def _unit_norm(unit: str | None) -> str:
    return re.sub(r"\s+", "", (unit or "").lower().replace("µ", "u").replace("μ", "u"))


def _flag_value(marker: BloodMarker) -> str:
    flag = marker.flag
    return str(getattr(flag, "value", flag) or "").lower()


def _status(marker: BloodMarker) -> tuple[str, str]:
    """The report's own flag wins. A range is only used when the report gave no flag."""
    if marker.value is None:
        return "no_value", "none"
    flag = _flag_value(marker)
    if flag in {"low", "high", "critical", "normal"}:
        return flag, "report_flag"
    low, high = marker.reference_low, marker.reference_high
    if low is not None and marker.value < low:
        return "low", "reference_range"
    if high is not None and marker.value > high:
        return "high", "reference_range"
    if low is not None or high is not None:
        return "normal", "reference_range"
    return "no_range", "none"


def _friendly(name: str) -> str:
    spelling = load_registry().spelling

    def fix(match: re.Match) -> str:
        right = spelling[match.group(0).lower()]
        return right.capitalize() if match.group(0)[:1].isupper() else right

    pattern = re.compile("|".join(re.escape(wrong) for wrong in spelling), re.I) if spelling else None
    cleaned = pattern.sub(fix, name) if pattern else name
    return re.sub(r"\s+", " ", cleaned).strip()


def _identity(resolution: Resolution, marker: BloodMarker) -> tuple:
    if resolution.canonical_id:
        return ("canonical", resolution.canonical_id)
    return ("raw", normalize_label(marker.name, load_registry().spelling))


def _same_test(a: _Record, b: _Record) -> bool:
    if a.identity != b.identity or a.unit_n != b.unit_n:
        return False
    return not (a.group_n and b.group_n and a.group_n != b.group_n)


def _same_result(a: _Record, b: _Record) -> bool:
    ma, mb = a.marker, b.marker
    return (
        ma.value == mb.value
        and ma.reference_low == mb.reference_low
        and ma.reference_high == mb.reference_high
        and a.status == b.status
    )


def _records(report: BloodReport) -> list[_Record]:
    reg = load_registry()
    out: list[_Record] = []
    seen_ids: dict[str, int] = defaultdict(int)
    for index, marker in enumerate(report.markers):
        resolution = resolve_marker(marker.name, marker.key, marker.category)
        status, source = _status(marker)
        base = f"{report.report_id}:{marker.id or index}"
        seen_ids[base] += 1
        result_id = base if seen_ids[base] == 1 else f"{base}#{seen_ids[base]}"
        out.append(
            _Record(
                marker=marker,
                index=index,
                resolution=resolution,
                result_id=result_id,
                status=status,
                status_source=source,
                identity=_identity(resolution, marker),
                group_n=normalize_label(marker.category or "", reg.spelling),
                unit_n=_unit_norm(marker.unit),
            )
        )
    return out


def _collapse(records: list[_Record]) -> list[_Record]:
    """One record per test. Exact repeats collapse. A repeat with a different value keeps the
    first result with a value and lists the other values, so nothing is averaged or lost."""
    kept: list[_Record] = []
    for record in records:
        twin = next((k for k in kept if _same_test(k, record)), None)
        if twin is None:
            kept.append(record)
            continue
        twin.duplicates += 1
        if _same_result(twin, record):
            continue
        if twin.marker.value is None and record.marker.value is not None:
            record.duplicates = twin.duplicates
            record.conflicts = list(twin.conflicts)
            kept[kept.index(twin)] = record
            continue
        value = record.marker.value
        if value is not None and value != twin.marker.value and value not in twin.conflicts:
            twin.conflicts.append(float(value))
    return kept


def _history(record: _Record, earlier: list[tuple[BloodReport, list[_Record]]]):
    """Earlier results for the same test with the same unit, oldest first. Different units are
    never mixed into one trend."""
    points: list[HistoryPoint] = []
    unit_changed = False
    for report, rows in earlier:
        for row in rows:
            if row.identity != record.identity or row.marker.value is None:
                continue
            if row.unit_n != record.unit_n:
                unit_changed = True
                continue
            if row.group_n and record.group_n and row.group_n != record.group_n:
                continue
            points.append(HistoryPoint(date=str(report.report_date), value=float(row.marker.value), status=row.status))
            break
    return points, unit_changed


def _result(
    record: _Record,
    report: BloodReport,
    earlier: list[tuple[BloodReport, list[_Record]]],
) -> BiomarkerResult:
    marker, res = record.marker, record.resolution
    measured = _day(marker.measured_at) or str(report.report_date)
    points, unit_changed = _history(record, earlier)
    previous = points[-1] if points else None
    trend = change = None
    if marker.value is not None and previous is not None:
        trend = _trend(float(marker.value), previous.value, marker.reference_low, marker.reference_high)
        change = (
            "unchanged"
            if marker.value == previous.value
            else "increased"
            if marker.value > previous.value
            else "decreased"
        )
    history = list(points)
    if marker.value is not None and points:
        history.append(HistoryPoint(date=measured, value=float(marker.value), status=record.status))
    note = None
    if unit_changed and not points:
        note = "An earlier result used a different unit, so it is not compared."
    elif unit_changed:
        note = "Earlier results in a different unit are left out of this trend."
    return BiomarkerResult(
        result_id=record.result_id,
        original_name=marker.name,
        display_name=_friendly(marker.name),
        canonical_id=res.canonical_id,
        cura_key=marker.key,
        source_group=marker.category,
        system_id=res.primary_system,
        secondary_system_ids=list(res.secondary_systems),
        value=marker.value,
        unit=marker.unit,
        reference_low=marker.reference_low,
        reference_high=marker.reference_high,
        status=record.status,
        status_source=record.status_source,
        report_flag=_flag_value(marker) or None,
        measured_on=measured,
        report_id=marker.report_id or report.report_id,
        is_derived=res.derived,
        mapping_method=res.method,
        needs_mapping_review=res.needs_mapping_review,
        note=res.review_note,
        duplicates_collapsed=record.duplicates,
        conflicting_values=record.conflicts,
        previous_value=previous.value if previous else None,
        previous_on=previous.date if previous else None,
        trend=trend,
        change=change,
        history=history,
        history_note=note,
    )


def _breakdown(results: list[BiomarkerResult]) -> StatusBreakdown:
    counts = StatusBreakdown()
    for item in results:
        setattr(counts, item.status, getattr(counts, item.status) + 1)
    return counts


def _gap(item: BiomarkerResult) -> float:
    if item.value is None:
        return 0.0
    if item.reference_high is not None and item.value > item.reference_high and item.reference_high:
        return (item.value - item.reference_high) / abs(item.reference_high)
    if item.reference_low is not None and item.value < item.reference_low and item.reference_low:
        return (item.reference_low - item.value) / abs(item.reference_low)
    return 0.0


def _key_findings(results: list[BiomarkerResult], limit: int = 3) -> list[KeyFinding]:
    flagged = [item for item in results if item.status in _ABNORMAL and not item.is_derived]
    flagged.sort(key=lambda item: (_SEVERITY[item.status], -_gap(item), item.display_name.lower()))
    return [
        KeyFinding(
            result_id=item.result_id,
            label=item.display_name,
            value=item.value,
            unit=item.unit,
            status=item.status,
            how_far=how_far(item.value, item.reference_low, item.reference_high),
        )
        for item in flagged[:limit]
    ]


def _state(counts: StatusBreakdown, total: int) -> str:
    abnormal = counts.low + counts.high + counts.critical
    if abnormal:
        return "attention"
    if counts.no_value == total:
        return "no_values"
    if counts.normal == total:
        return "all_in_range"
    return "partly_assessed"


def _group_coverage(results: list[BiomarkerResult], observed: set[str]) -> list[GroupCoverage]:
    """How much of each source test group this report holds. Only groups with results are listed."""
    reg = load_registry()
    per_group: dict[str, set[str]] = defaultdict(set)
    for item in results:
        if not item.canonical_id:
            continue
        group_n = normalize_label(item.source_group or "", reg.spelling)
        if group_n in reg.group_tests and item.canonical_id in reg.group_tests[group_n]:
            per_group[group_n].add(item.canonical_id)
            continue
        options = [g for g, ids in reg.group_tests.items() if item.canonical_id in ids]
        if not options:
            continue
        options.sort(key=lambda g: (-len(observed & reg.group_tests[g]), len(reg.group_tests[g]), g))
        per_group[options[0]].add(item.canonical_id)
    coverage = [
        GroupCoverage(
            source_group=reg.group_names[group],
            observed_count=len(ids),
            registry_count=len(reg.group_tests[group]),
            partial=len(ids) < len(reg.group_tests[group]),
        )
        for group, ids in per_group.items()
    ]
    return sorted(coverage, key=lambda item: item.source_group)


def _summary(
    system: BodySystem,
    own: list[BiomarkerResult],
    related: list[BiomarkerResult],
    observed: set[str],
) -> SystemSummary:
    counting = related if system.related_only else own
    counts = _breakdown(counting)
    latest = max((item.measured_on for item in counting if item.measured_on), default=None)
    return SystemSummary(
        id=system.id,
        name=system.name,
        scope="related_only" if system.related_only else "primary",
        about=system.about,
        caveat=system.caveat,
        available_count=len(counting),
        abnormal_count=counts.low + counts.high + counts.critical,
        status_breakdown=counts,
        state=_state(counts, len(counting)),
        key_findings=_key_findings(counting),
        result_ids=[] if system.related_only else [item.result_id for item in own],
        related_result_ids=[item.result_id for item in related],
        related_abnormal_count=sum(1 for item in related if item.status in _ABNORMAL),
        group_coverage=[] if system.related_only else _group_coverage(own, observed),
        latest_measured_on=latest,
        needs_mapping_review=system.id == OTHER_ID,
    )


def _allergy_section(results: list[BiomarkerResult]) -> SystemSummary | None:
    if not results:
        return None
    reg = load_registry()
    subsection_of = {normalize_label(g.group, reg.spelling): g.subsection for g in reg.allergy_groups}
    grouped: dict[str, list[BiomarkerResult]] = defaultdict(list)
    for item in results:
        key = normalize_label(item.source_group or item.original_name, reg.spelling)
        grouped[subsection_of.get(key, "Allergy")].append(item)
    subsections = [
        AllergySubsection(
            name=name,
            source_groups=sorted({item.source_group or item.original_name for item in items}),
            result_ids=[item.result_id for item in items],
            available_count=len(items),
            abnormal_count=sum(1 for item in items if item.status in _ABNORMAL),
        )
        for name, items in sorted(grouped.items())
    ]
    counts = _breakdown(results)
    return SystemSummary(
        id=ALLERGY_ID,
        name=ALLERGY_NAME,
        about=ALLERGY_ABOUT,
        caveat="Allergy results show sensitisation on a test. They are not a diagnosis of an allergy.",
        available_count=len(results),
        abnormal_count=counts.low + counts.high + counts.critical,
        status_breakdown=counts,
        state=_state(counts, len(results)),
        key_findings=_key_findings(results),
        result_ids=[item.result_id for item in results],
        latest_measured_on=max((item.measured_on for item in results if item.measured_on), default=None),
        subsections=subsections,
    )


def _ref(report: BloodReport) -> ReportRef:
    return ReportRef(report_id=report.report_id, report_date=str(report.report_date), source_line="blood")


def build_body_system_overview(reports: list[BloodReport], report_id: str | None = None) -> BodySystemOverview:
    reg = load_registry()
    ordered = sorted(reports or [], key=lambda r: (r.report_date, r.report_id))
    if not ordered:
        return BodySystemOverview(available=False, state="no_report", registry_version=reg.version)
    refs = [_ref(r) for r in reversed(ordered)]
    if report_id:
        selected = next((r for r in ordered if r.report_id == report_id), None)
        if selected is None:
            raise ReportNotFound(report_id)
    else:
        selected = ordered[-1]

    earlier_reports = [r for r in ordered if r.report_date < selected.report_date]
    earlier = [(r, _collapse(_records(r))) for r in earlier_reports]
    records = _collapse(_records(selected))
    collapsed_total = sum(record.duplicates for record in records)
    if not records:
        return BodySystemOverview(
            available=True,
            state="no_results",
            registry_version=reg.version,
            report=_ref(selected),
            available_reports=refs,
        )

    results = [_result(record, selected, earlier) for record in records]
    observed = {item.canonical_id for item in results if item.canonical_id}

    allergy = [item for item in results if item.system_id == ALLERGY_ID]
    body = [item for item in results if item.system_id != ALLERGY_ID]
    by_system: dict[str, list[BiomarkerResult]] = defaultdict(list)
    for item in body:
        by_system[item.system_id].append(item)
    related_by_system: dict[str, list[BiomarkerResult]] = defaultdict(list)
    for item in body:
        for system_id in item.secondary_system_ids:
            related_by_system[system_id].append(item)

    summaries: list[SystemSummary] = []
    for system in SYSTEMS:
        own = by_system.get(system.id, [])
        related = related_by_system.get(system.id, [])
        if system.related_only:
            if not related:
                continue
        elif not own:
            continue
        summaries.append(_summary(system, own, related, observed))
    if by_system.get(OTHER_ID):
        summaries.append(_summary(OTHER, by_system[OTHER_ID], [], observed))
    # Systems that need attention first; the registry order breaks ties and never changes the set shown.
    order = {system.id: system.order for system in (*SYSTEMS, OTHER)}
    summaries.sort(key=lambda item: (item.id == OTHER_ID, item.scope == "related_only", item.abnormal_count == 0, order[item.id]))

    unmapped = [item for item in results if item.needs_mapping_review]
    if unmapped:
        logger.warning("biomarker_mapping_review count=%d names=%s", len(unmapped), sorted({i.original_name for i in unmapped})[:20])

    totals = ReportTotals(
        unique_results=len(results),
        abnormal=sum(1 for item in results if item.status in _ABNORMAL),
        status_breakdown=_breakdown(results),
        unmapped=len(unmapped),
        allergy=len(allergy),
        duplicates_collapsed=collapsed_total,
        conflicting_duplicates=sum(1 for item in results if item.conflicting_values),
    )
    return BodySystemOverview(
        available=True,
        state="ready",
        registry_version=reg.version,
        report=_ref(selected),
        available_reports=refs,
        totals=totals,
        systems=summaries,
        allergy=_allergy_section(allergy),
        results=results,
    )

