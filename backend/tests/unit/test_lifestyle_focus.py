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
