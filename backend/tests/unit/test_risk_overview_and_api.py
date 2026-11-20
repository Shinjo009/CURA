"""Bio-AI predicted-risk overview and the two overview endpoints."""

from __future__ import annotations

from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.biomarkers.overview import ReportNotFound
from app.biomarkers.risk_overview import DISCLAIMER, build_risk_overview
from app.contracts.bio_ai import BioAIReport, BioAIRisk
from app.core.errors import ProviderUnavailableError
from app.main import app
from app.pipeline.answer_consistency import _RAISED
from app.providers.registry import get_registry

client = TestClient(app)


def risk(code, status, score=None, name=None, **extra):
    return BioAIRisk(code=code, name=name or code.replace("_", " ").title(), status=status, score=score, **extra)


def bio(risks, rid="b1", day=date(2026, 8, 18), line="bio_ai"):
    return BioAIReport(report_id=rid, report_date=day, source_line=line, risks=risks)


def groups(overview):
    return {g.id: g for g in overview.groups}


def test_groups_are_built_only_from_risks_the_report_returned():
    ov = build_risk_overview([bio([risk("cardiac_health", "moderate", 30), risk("nafld", "mild", 12)])])
    assert set(groups(ov)) == {"heart_circulation", "liver_health"}
    assert ov.totals.risk_count == 2 and ov.totals.raised_count == 1


def test_a_single_risk_yields_a_single_group():
    ov = build_risk_overview([bio([risk("thyroid", "low", 8)])])
    assert [g.id for g in ov.groups] == ["thyroid_health"] and ov.totals.raised_count == 0


def test_no_bio_ai_report_gives_an_empty_overview():
    ov = build_risk_overview([])
    assert (ov.available, ov.state, ov.groups, ov.risks) == (False, "no_report", [], [])
    assert ov.disclaimer == DISCLAIMER


def test_report_without_risks_is_not_a_clean_bill_of_health():
    ov = build_risk_overview([bio([])])
    assert ov.state == "no_results" and ov.groups == []


def test_predictions_are_labelled_as_predicted_risk_not_diagnosis_or_measurement():
    ov = build_risk_overview([bio([risk("type_2_diabetes", "high", 61)])])
    assert ov.risks[0].kind == "predicted_risk"
    assert "not measured blood results" in ov.disclaimer and "not diagnoses" in ov.disclaimer


def test_unknown_risk_codes_are_kept_in_a_review_group():
    ov = build_risk_overview([bio([risk("zorb_syndrome", "high", 70, name="Zorb syndrome")])])
    assert groups(ov)["other_risks"].needs_mapping_review is True
    assert ov.risks[0].name == "Zorb syndrome" and ov.risks[0].score == 70


def test_repeated_risk_codes_count_once():
    ov = build_risk_overview([bio([risk("nafld", "mild", None), risk("nafld", "moderate", 22, name="Fatty liver (NAFLD)")])])
    assert ov.totals.risk_count == 1 and ov.totals.duplicates_collapsed == 1
    assert ov.risks[0].score == 22


def test_raised_uses_the_same_statuses_as_the_chat_answers():
    statuses = ["critical", "very high", "high", "elevated", "moderate", "medium", "mild", "low", None]
    ov = build_risk_overview([bio([risk(f"x{i}", s) for i, s in enumerate(statuses)])])
    expected = sum(1 for s in statuses if (s or "").lower() in _RAISED)
    assert ov.totals.raised_count == expected
    assert next(r for r in ov.risks if r.status is None).level == "unknown"


def test_scores_percentiles_and_factors_pass_through_unchanged():
    ov = build_risk_overview(
        [bio([risk("cardiac_health", "moderate", 30.5, percentile=55, lifestyle_contribution=40, contributing_factors=["LDL", "Activity"])])]
    )
    item = ov.risks[0]
    assert (item.score, item.percentile, item.lifestyle_contribution) == (30.5, 55, 40)
    assert item.contributing_factors == ["LDL", "Activity"] and item.measured_on == "2026-08-18"


def test_same_day_reports_are_flagged_so_the_member_can_choose():
    a = bio([risk("cardiac_health", "high", 70)], rid="a", line="bio_ai")
    b = bio([risk("cardiac_health", "mild", 20)], rid="b", line="advanced_bio_ai")
    ov = build_risk_overview([a, b])
    assert ov.same_day_alternatives is True
    assert {r.report_id for r in ov.available_reports} == {"a", "b"}
    chosen = build_risk_overview([a, b], report_id="a")
    assert chosen.risks[0].score == 70


def test_previous_score_comes_only_from_an_earlier_report():
    old = bio([risk("cardiac_health", "moderate", 40)], rid="old", day=date(2026, 1, 1))
    new = bio([risk("cardiac_health", "mild", 25)], rid="new")
    item = build_risk_overview([old, new]).risks[0]
    assert item.previous_score == 40 and item.change == "decreased" and [p.score for p in item.history] == [40, 25]
    assert build_risk_overview([old, new], report_id="old").risks[0].previous_score is None


def test_unknown_bio_ai_report_id_raises():
    with pytest.raises(ReportNotFound):
        build_risk_overview([bio([risk("nafld", "low")])], report_id="zzz")


def test_blood_results_never_create_a_predicted_risk():
    # The risk overview takes Bio-AI reports only; a report without a thyroid risk has no thyroid card.
    ov = build_risk_overview([bio([risk("cardiac_health", "moderate", 30)])])
    assert "thyroid_health" not in groups(ov)


# ---- endpoints ----------------------------------------------------------------------------

AS_DEMO = {"X-Cura-User-Id": "demo-user-001"}


def test_endpoints_require_auth():
    assert client.get("/api/v1/me/body-systems").status_code == 401
    assert client.get("/api/v1/me/bio-ai-risks").status_code == 401


def test_body_systems_endpoint_builds_from_the_members_report():
    body = client.get("/api/v1/me/body-systems", headers=AS_DEMO).json()
    assert body["state"] == "ready" and body["totals"]["unique_results"] == len(body["results"])
    assert sum(s["available_count"] for s in body["systems"] if s["scope"] == "primary") == len(body["results"])
    assert body["registry_version"]


def test_a_member_with_no_reports_gets_an_empty_overview():
    body = client.get("/api/v1/me/body-systems", headers={"X-Cura-User-Id": "no-such-member"}).json()
    assert body["state"] == "no_report" and body["systems"] == []
    risks = client.get("/api/v1/me/bio-ai-risks", headers={"X-Cura-User-Id": "no-such-member"}).json()
    assert risks["state"] == "no_report" and risks["groups"] == []


def test_members_only_see_their_own_results():
    one = client.get("/api/v1/me/body-systems", headers=AS_DEMO).json()
    two = client.get("/api/v1/me/body-systems", headers={"X-Cura-User-Id": "demo-user-002"}).json()
    assert {r["result_id"] for r in one["results"]}.isdisjoint({r["result_id"] for r in two["results"]})


def test_report_id_selects_a_historical_report_and_an_unknown_id_is_404():
    older = client.get("/api/v1/me/body-systems?report_id=blood-001", headers=AS_DEMO).json()
    assert older["report"]["report_id"] == "blood-001"
    assert client.get("/api/v1/me/body-systems?report_id=nope", headers=AS_DEMO).status_code == 404
    assert client.get("/api/v1/me/bio-ai-risks?report_id=nope", headers=AS_DEMO).status_code == 404


def test_bio_ai_endpoint_separates_predictions_from_blood_results():
    body = client.get("/api/v1/me/bio-ai-risks", headers=AS_DEMO).json()
    assert body["state"] == "ready" and body["disclaimer"] == DISCLAIMER
    assert all(r["kind"] == "predicted_risk" for r in body["risks"])
    assert body["totals"]["risk_count"] == len(body["risks"])


def test_provider_outage_is_a_plain_503(monkeypatch):
    def down(*args, **kwargs):
        raise ProviderUnavailableError("db down")

    registry = get_registry()
    monkeypatch.setattr(registry.blood, "query", down)
    monkeypatch.setattr(registry.bio_ai, "query", down)
    for path in ("/api/v1/me/body-systems", "/api/v1/me/bio-ai-risks"):
        res = client.get(path, headers=AS_DEMO)
        assert res.status_code == 503 and "db down" not in res.text
