from types import SimpleNamespace

import pytest

from app.contracts.blood import BloodMarker
from app.pipeline.answer_plan import (
    AnswerPlan, Component, PlanIntent, Proportion, build_answer_plan, plan_prompt,
)


def _marker(key, name, value, low, high, flag):
    return BloodMarker(id=key, key=key, name=name, value=value, unit="x", reference_low=low, reference_high=high, flag=flag)


def _ctx(markers, *, turn=None, explained=(), kind="MARKER_LOOKUP", goal="interpret", intent="blood_marker_explanation", risks=()):
    return SimpleNamespace(
        markers=markers, bio_ai_risks=list(risks), task_contract={"response_type": kind, "goal": goal},
        intent=SimpleNamespace(value=intent), conversation_turn=turn, facts_already_explained=list(explained),
        explained_entities=[], comparisons=[],
    )


def test_tiny_gap_is_minor_and_brief_and_never_a_goal_to_chase():
    urea = _marker("urea", "Urea", 16.72, 17.0, 43.0, "low")
    plan = build_answer_plan(_ctx([urea]), "What does my Urea result mean?")
    assert plan.intent == PlanIntent.personal_interpretation
    assert plan.proportion == Proportion.minor and plan.detail_level == "brief"
    assert "goal_to_raise_or_lower_waste_marker" in plan.must_not_claim
    text = plan_prompt(plan)
    assert "only slightly outside" in text and "routine recheck" in text
    assert "Never suggest raising or lowering" in text


def test_large_gap_is_marked_and_escalates():
    vit_d = _marker("vitamin_d", "Vitamin D", 12.6, 30.0, 100.0, "low")
    plan = build_answer_plan(_ctx([vit_d]), "What does my Vitamin D result mean?")
    assert plan.proportion == Proportion.marked
    assert Component.escalation in plan.components and Component.mechanism in plan.components


def test_in_range_is_short_and_skips_cause_and_escalation():
    hba1c = _marker("hba1c", "HbA1c", 5.5, 4.0, 5.6, "normal")
    plan = build_answer_plan(_ctx([hba1c]), "What does my HbA1c mean?")
    assert plan.proportion == Proportion.within_range
    assert Component.mechanism not in plan.components and Component.escalation not in plan.components


def test_food_follow_up_does_not_repeat_the_explanation():
    urea = _marker("urea", "Urea", 16.72, 17.0, 43.0, "low")
    ctx = _ctx([urea], turn="FOLLOW_UP_QUESTION", explained=["Urea"])
    plan = build_answer_plan(ctx, "Which protein foods fit my usual vegetarian meals?")
    assert plan.intent == PlanIntent.follow_up and plan.follow_up
    assert plan.components == [Component.next_steps]
    text = plan_prompt(plan)
    assert "do not explain it again: Urea" in text and "Answer only the new question" in text


def test_missing_range_is_recorded_as_missing_evidence():
    m = _marker("x", "Mystery", 5.0, None, None, "unknown")
    plan = build_answer_plan(_ctx([m]), "What does my Mystery result mean?")
    assert "laboratory_reference_interval" in plan.missing_evidence


def test_plan_carries_no_values_or_report_text():
    urea = _marker("urea", "Urea", 16.72, 17.0, 43.0, "low")
    dumped = build_answer_plan(_ctx([urea]), "What does my Urea result mean?").model_dump_json()
    assert "16.72" not in dumped and "17.0" not in dumped


def test_unknown_plan_values_are_rejected():
    with pytest.raises(Exception):
        AnswerPlan(intent="not_an_intent")


@pytest.mark.parametrize("mode", ["off", "shadow", "on"])
def test_modes_never_break_the_prompt(monkeypatch, mode):
    from fastapi.testclient import TestClient

    from app.core.config import settings
    from app.main import app
    from app.pipeline import prompt_modules as pm

    monkeypatch.setattr(settings, "answer_plan_mode", mode)
    monkeypatch.setattr(settings, "cura_prompt_variant", "house")
    monkeypatch.setattr(settings, "enable_llm", True)
    seen = {}
    original = pm.house_system

    def spy(context, message):
        out = original(context, message)
        seen["system"] = out
        return out

    monkeypatch.setattr(pm, "house_system", spy)
    res = TestClient(app).post("/api/v1/chat", headers={"X-Cura-User-Id": "demo-user-001"}, json={"message": "What does my latest HbA1c mean?"})
    assert res.status_code == 200
    assert seen["system"].startswith("You are the SuperShyft Health Assistant")
    assert ("ANSWER PLAN" in seen["system"]) == (mode == "on")


def test_plain_result_question_is_not_a_trend_just_because_an_earlier_report_exists():
    vit_d = _marker("vitamin_d", "Vitamin D", 12.6, 30.0, 100.0, "low")
    ctx = _ctx([vit_d])
    ctx.comparisons = [object()]
    assert build_answer_plan(ctx, "What does my latest Vitamin D result mean?").intent == PlanIntent.personal_interpretation
    assert build_answer_plan(ctx, "Has my Vitamin D improved since last time?").intent == PlanIntent.trend


def test_already_explained_names_are_plain_words():
    urea = _marker("urea", "Urea", 16.72, 17.0, 43.0, "low")
    ctx = _ctx([urea], turn="FOLLOW_UP_QUESTION", explained=["vitamin_d"])
    assert "vitamin d" in plan_prompt(build_answer_plan(ctx, "Which foods can help?"))
    assert "vitamin_d" not in plan_prompt(build_answer_plan(ctx, "Which foods can help?"))
