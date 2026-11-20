"""Body-system and Bio-AI risk overviews.

Built from structured report data only, with no model call. Every value, unit, reference range,
flag and date is the report's own. Counts count each result record once: a result that is also
related to a second system is listed there by id and never counted again.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

ResultStatus = Literal["normal", "low", "high", "critical", "no_range", "no_value"]
SystemState = Literal["attention", "all_in_range", "partly_assessed", "no_values"]
OverviewState = Literal["ready", "no_report", "no_results"]


class ReportRef(BaseModel):
    report_id: str
    report_date: str
    source_line: str | None = None


class HistoryPoint(BaseModel):
    date: str
    value: float
    status: str = "unknown"


class BiomarkerResult(BaseModel):
    result_id: str
    original_name: str  # exactly as the laboratory report names it
    display_name: str  # same name with known spelling slips repaired
    canonical_id: str | None = None
    cura_key: str | None = None  # the key chat uses for this marker (marker_code)
    source_group: str | None = None
    system_id: str
    secondary_system_ids: list[str] = Field(default_factory=list)
    value: float | None = None
    unit: str | None = None
    reference_low: float | None = None
    reference_high: float | None = None
    status: ResultStatus
    status_source: Literal["report_flag", "reference_range", "none"] = "none"
    report_flag: str | None = None
    measured_on: str | None = None
    report_id: str | None = None
    is_derived: bool = False
    mapping_method: str = "unmapped"
    needs_mapping_review: bool = False
    note: str | None = None
    # The same test listed more than once in this report.
    duplicates_collapsed: int = 0
    conflicting_values: list[float] = Field(default_factory=list)
    # History across earlier reports, only where unit and test match.
    previous_value: float | None = None
    previous_on: str | None = None
    trend: Literal["toward_range", "away_from_range", "steady", "in_range"] | None = None
    change: Literal["increased", "decreased", "unchanged"] | None = None
    history: list[HistoryPoint] = Field(default_factory=list)
    history_note: str | None = None


class StatusBreakdown(BaseModel):
    normal: int = 0
    low: int = 0
    high: int = 0
    critical: int = 0
    no_range: int = 0
    no_value: int = 0


class KeyFinding(BaseModel):
    result_id: str
    label: str
    value: float | None = None
    unit: str | None = None
    status: ResultStatus
    how_far: Literal["slightly", "moderately", "clearly"] | None = None


class GroupCoverage(BaseModel):
    source_group: str
    observed_count: int
    registry_count: int
    partial: bool


class AllergySubsection(BaseModel):
    name: str
    source_groups: list[str]
    result_ids: list[str]
    available_count: int
    abnormal_count: int


class SystemSummary(BaseModel):
    id: str
    name: str
    scope: Literal["primary", "related_only"] = "primary"
    about: str = ""
    caveat: str | None = None
    available_count: int
    abnormal_count: int
    status_breakdown: StatusBreakdown
    state: SystemState
    key_findings: list[KeyFinding] = Field(default_factory=list)
    result_ids: list[str] = Field(default_factory=list)
    related_result_ids: list[str] = Field(default_factory=list)
    related_abnormal_count: int = 0
    group_coverage: list[GroupCoverage] = Field(default_factory=list)
    latest_measured_on: str | None = None
    needs_mapping_review: bool = False
    subsections: list[AllergySubsection] = Field(default_factory=list)


class ReportTotals(BaseModel):
    unique_results: int = 0
    abnormal: int = 0
    status_breakdown: StatusBreakdown = Field(default_factory=StatusBreakdown)
    unmapped: int = 0
    allergy: int = 0
    duplicates_collapsed: int = 0
    conflicting_duplicates: int = 0


class BodySystemOverview(BaseModel):
    available: bool = False
    state: OverviewState = "no_report"
    registry_version: str
    report: ReportRef | None = None
    available_reports: list[ReportRef] = Field(default_factory=list)
    totals: ReportTotals = Field(default_factory=ReportTotals)
    systems: list[SystemSummary] = Field(default_factory=list)
    allergy: SystemSummary | None = None
    results: list[BiomarkerResult] = Field(default_factory=list)


# ---- Bio-AI predicted risks: a separate registry, never inferred from blood results ----

RiskLevel = Literal["raised", "not_raised", "unknown"]


class RiskHistoryPoint(BaseModel):
    date: str
    score: float | None = None
    status: str | None = None


class RiskResult(BaseModel):
    code: str
    name: str
    group_id: str
    kind: Literal["predicted_risk"] = "predicted_risk"
    score: float | None = None
    status: str | None = None  # the report's own wording
    level: RiskLevel = "unknown"
    percentile: float | None = None
    lifestyle_contribution: float | None = None
    contributing_factors: list[str] = Field(default_factory=list)
    measured_on: str | None = None
    report_id: str | None = None
    previous_score: float | None = None
    previous_on: str | None = None
    change: Literal["increased", "decreased", "unchanged"] | None = None
    history: list[RiskHistoryPoint] = Field(default_factory=list)
    duplicates_collapsed: int = 0


class RiskKeyFinding(BaseModel):
    code: str
    name: str
    score: float | None = None
    status: str | None = None


class RiskGroupSummary(BaseModel):
    id: str
    name: str
    about: str = ""
    risk_count: int
    raised_count: int
    status_breakdown: dict[str, int] = Field(default_factory=dict)
    key_findings: list[RiskKeyFinding] = Field(default_factory=list)
    risk_codes: list[str] = Field(default_factory=list)
    needs_mapping_review: bool = False


class RiskReportRef(ReportRef):
    metabolic_age: float | None = None
    metabolic_score: float | None = None


class RiskTotals(BaseModel):
    risk_count: int = 0
    raised_count: int = 0
    duplicates_collapsed: int = 0


class RiskOverview(BaseModel):
    available: bool = False
    state: OverviewState = "no_report"
    registry_version: str
    disclaimer: str
    report: RiskReportRef | None = None
    available_reports: list[ReportRef] = Field(default_factory=list)
    same_day_alternatives: bool = False
    totals: RiskTotals = Field(default_factory=RiskTotals)
    groups: list[RiskGroupSummary] = Field(default_factory=list)
    risks: list[RiskResult] = Field(default_factory=list)
