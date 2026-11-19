import pytest

from app.pipeline.prompt_modules import is_lifestyle_topic_question, RESULT_WALKTHROUGH, LIFESTYLE_FOCUS


@pytest.mark.parametrize("message", [
    "What does my sleep pattern say about my health?",
    "How is my stress affecting my health?",
    "Is my exercise routine enough?",
])
def test_habit_questions_are_lifestyle_focused(message):
    assert is_lifestyle_topic_question(message)


@pytest.mark.parametrize("message", [
    "Does my sleep explain my low vitamin D?",
    "What does my Alkaline Phosphatase result mean?",
    "Explain my blood report",
    "How does stress change my Bio-AI score?",
    "Is my exercise routine why my cholesterol is high?",
])
def test_lab_questions_are_not_lifestyle_focused(message):
    assert not is_lifestyle_topic_question(message)


def test_walkthrough_has_the_six_parts_in_order():
    parts = ["What the test is", "What your result says", "How far outside", "What could explain it", "Should you worry", "What to do now"]
    positions = [RESULT_WALKTHROUGH.index(p) for p in parts]
    assert positions == sorted(positions)
    assert "—" not in RESULT_WALKTHROUGH and "–" not in RESULT_WALKTHROUGH and "—" not in LIFESTYLE_FOCUS


def test_food_follow_up_does_not_get_the_result_walkthrough():
    from types import SimpleNamespace
    from app.pipeline.prompt_modules import is_result_walkthrough

    ctx = SimpleNamespace(task_contract={"response_type": "MARKER_LOOKUP", "goal": "interpret"}, intent=SimpleNamespace(value="blood_marker_explanation"), markers=[object()])
    assert is_result_walkthrough(ctx, "What does my Urea result mean?")
    assert not is_result_walkthrough(ctx, "Which protein foods fit my usual vegetarian meals to raise urea?")
    assert not is_result_walkthrough(ctx, "How can I improve my vitamin D?")


def test_marker_after_my_must_be_what_my_points_at():
    from app.pipeline.task_contract import _names_own_marker

    assert _names_own_marker("What does my Urea result mean?")
    assert _names_own_marker("is my cholestrol normal?")
    assert not _names_own_marker("Which protein foods fit my usual vegetarian meals to raise urea?")
    assert not _names_own_marker("What does cholesterol do in my body?")


def test_praise_opener_and_bullet_labels_are_removed_but_bold_labels_and_values_stay():
    from app.pipeline.markdown_tidy import drop_bullet_labels, drop_praise_opener

    text = "Thanks, great question about foods you can use.\n\n- Worry level: usually low.\n- One simple step: add dal.\n- **What to do first:** walk daily.\n- Urea: 16.7 mg/dL is a bit low."
    out = drop_bullet_labels(drop_praise_opener(text))
    assert out.startswith("- Usually low.")
    assert "- Add dal." in out
    assert "**What to do first:** walk daily." in out
    assert "- Urea: 16.7 mg/dL" in out
