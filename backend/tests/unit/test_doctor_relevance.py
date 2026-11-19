from app.pipeline.markdown_tidy import drop_routine_doctor
from app.pipeline.prompt_modules import HOUSE_CORE


def test_routine_visit_filler_is_dropped():
    text = "- Your ALP is 120, slightly above range. Share these scores with your doctor at your next routine visit.\n- Discuss this with your doctor."
    out = drop_routine_doctor(text)
    assert "routine visit" not in out and "Discuss this" not in out
    assert "ALP is 120" in out


def test_real_referral_is_kept():
    text = "- Your LDL is far above range. See a doctor within a few weeks and bring this report."
    assert drop_routine_doctor(text) == text


def test_prompt_does_not_force_a_doctor_bullet():
    assert "One of them says how soon to see a doctor" not in HOUSE_CORE
    assert "goes in the last bullet" not in HOUSE_CORE


def test_narrow_questions_skip_report_layouts():
    from types import SimpleNamespace
    from app.contracts.common import IntentType
    from app.pipeline.prompt_modules import core_for
    narrow = SimpleNamespace(intent=IntentType.blood_marker_explanation)
    wide = SimpleNamespace(intent=IntentType.broad_health_summary)
    assert "SHAPE 1A, a whole" not in core_for(narrow, "What is urea?") and "SHAPE 2" in core_for(narrow, "What is urea?")
    assert "SHAPE 1A, a whole" in core_for(wide, "Explain my report")
