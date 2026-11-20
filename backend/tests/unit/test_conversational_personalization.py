"""Tone, rewrite, language continuity and plain talk. These check behavior and prompt directives, not exact wording."""

from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient

from app.contracts.common import AnswerDepth, IntentType
from app.contracts.conversation_state import ConversationState, TurnType
from app.contracts.health_context import HealthContext
from app.db.models import Conversation
from app.db.session import SessionLocal
from app.main import app
from app.pipeline.conversation_state import ConversationStateResolver, persistable_state
from app.pipeline.markdown_tidy import drop_hype_and_blame, soften_robotic_phrases
from app.pipeline.prompt_builder import _adaptive_response_brief
from app.pipeline.tone_signals import (
    ANGLES,
    CURIOUS,
    DETAILED,
    FRUSTRATED,
    NEUTRAL,
    QUICK,
    WORRIED,
    detect_tone,
    follow_up_limit,
    is_rewrite_request,
    pick_angle,
    tone_brief,
    trim_follow_ups,
)
from app.pipeline.translation import sticky_target_language

client = TestClient(app)
H = {"X-Cura-User-Id": "demo-user-001"}


def chat(message: str, conversation_id: str | None = None):
    return client.post("/api/v1/chat", headers=H, json={"message": message, "conversation_id": conversation_id}).json()


# ---- tone ----

@pytest.mark.parametrize(
    "message,tone",
    [
        ("My HbA1c is high. Does that mean I have diabetes?", WORRIED),
        ("I'm really scared about my LDL", WORRIED),
        ("mujhe bahut chinta ho rahi hai", WORRIED),
        ("I still don't understand what you're saying", FRUSTRATED),
        ("this is too technical", FRUSTRATED),
        ("Why does cholesterol increase?", CURIOUS),
        ("Is my vitamin D normal?", QUICK),
        ("give me a short answer", QUICK),
        ("Explain everything about my lipid profile", DETAILED),
        ("What should I eat?", NEUTRAL),
    ],
)
def test_tone_is_read_from_the_message(message, tone):
    assert detect_tone(message).tone == tone


def test_frustration_wins_over_worry():
    assert detect_tone("I'm worried and I still don't understand").tone == FRUSTRATED


@pytest.mark.parametrize(
    "message",
    ["Explain that more simply", "I still don't understand", "can you say that in simple words", "explain it differently please"],
)
def test_rewrite_requests_are_recognised(message):
    assert detect_tone(message).wants_rewrite is True


@pytest.mark.parametrize(
    "message",
    ["Why is mine high?", "What does ALT mean?", "What should I avoid?"],
)
def test_ordinary_follow_ups_are_not_rewrites(message):
    assert detect_tone(message).wants_rewrite is False


def test_a_message_with_its_own_topic_is_not_a_rewrite():
    assert is_rewrite_request("explain HbA1c more simply", mentions_topic=True) is False
    assert is_rewrite_request("explain this in a very long and elaborate way " * 3) is False


def test_each_rewrite_uses_a_new_angle_and_then_cycles():
    tried: list[str] = []
    for _ in range(len(ANGLES)):
        angle = pick_angle(tried)
        assert angle not in tried
        tried.append(angle)
    assert pick_angle(tried) in ANGLES


def _context(**kwargs) -> HealthContext:
    return HealthContext(intent=IntentType.blood_marker_explanation, answer_depth=AnswerDepth.simple, **kwargs)


def test_prompt_brief_is_empty_for_an_ordinary_turn():
    assert tone_brief(_context(user_tone=NEUTRAL)) == ""


def test_worried_brief_asks_for_calm_and_no_false_reassurance():
    brief = tone_brief(_context(user_tone=WORRIED))
    assert "worried" in brief and "not a diagnosis" in brief and "false reassurance" in brief


def test_rewrite_brief_carries_the_previous_answer_and_keeps_facts_fixed():
    brief = tone_brief(
        _context(user_tone=FRUSTRATED, rewrite_previous_answer="Your ALT is 22 U/L.", rewrite_angle=ANGLES[0])
    )
    assert "Your ALT is 22 U/L." in brief
    assert "every number, unit, date and safety instruction exactly the same" in brief
    assert ANGLES[0] in brief


def test_rewrite_turn_does_not_also_say_do_not_define_again():
    ctx = _context(
        user_tone=FRUSTRATED,
        rewrite_previous_answer="Your ALT is 22 U/L.",
        rewrite_angle=ANGLES[1],
        explained_entities=["alt"],
    )
    brief = _adaptive_response_brief(ctx)
    assert "REWRITE" in brief and "Do not define these again" not in brief


def test_ordinary_turn_still_says_do_not_define_again():
    assert "Do not define these again" in _adaptive_response_brief(_context(explained_entities=["alt"]))


def test_follow_up_count_shrinks_for_people_who_are_lost_or_in_a_hurry():
    assert follow_up_limit(NEUTRAL) == 4
    assert follow_up_limit(QUICK) == 2
    assert follow_up_limit(FRUSTRATED) == 2
    assert follow_up_limit(NEUTRAL, rewrite=True) == 2
    assert follow_up_limit(WORRIED) == 3
    assert trim_follow_ups([1, 2, 3, 4], FRUSTRATED) == [1, 2]
    assert trim_follow_ups([1], NEUTRAL) == [1]


# ---- language continuity ----

def test_a_short_follow_up_keeps_the_conversation_language():
    assert sticky_target_language("why?", "hinglish") == "hinglish"
    assert sticky_target_language("aur LDL?", "hinglish") == "hinglish"


def test_a_real_english_message_is_a_switch():
    assert sticky_target_language("What should I eat to lower my cholesterol?", "hinglish") == "en"


def test_asking_for_english_is_a_switch_even_when_short():
    assert sticky_target_language("in english", "hinglish") == "en"


def test_the_message_language_beats_the_remembered_one():
    assert sticky_target_language("mera cholesterol high hai kya", "en") == "hinglish"


def test_no_prior_language_means_english_for_short_english():
    assert sticky_target_language("why?", None) == "en"
    assert sticky_target_language("why?", "en") == "en"


def test_an_explicit_language_choice_always_wins():
    assert sticky_target_language("why?", "hinglish", "en", "manual") == "en"


# ---- state carries across turns ----

def _conv(state: ConversationState) -> SimpleNamespace:
    return SimpleNamespace(
        conversation_state_json=state.model_dump_json(),
        follow_up_topic=None,
        current_report_id=None,
        current_marker_code=None,
        conversation_summary=None,
        messages=[],
    )


def test_resolver_carries_explanation_memory_and_language():
    prior = ConversationState(
        active_entities=["alt"], previous_user_question="What does ALT mean?",
        explanations_tried=[ANGLES[0]], frustration_count=1, reply_language="hinglish",
    )
    resolved = ConversationStateResolver().resolve("why is mine high?", _conv(prior))
    assert resolved.explanations_tried == [ANGLES[0]]
    assert resolved.frustration_count == 1
    assert resolved.reply_language == "hinglish"


def test_a_topic_switch_forgets_the_old_explanations():
    resolved = ConversationState(
        turn_type=TurnType.topic_switch, explanations_tried=[ANGLES[0]], frustration_count=2, reply_language="hi"
    )
    state = persistable_state(
        resolved, plan_topic=None, plan_domains=[], plan_entities=[], plan_intent=None, user_message="x",
        assistant_summary=None, follow_up=None, expected_reply_type=resolved.expected_reply_type,
        expected_handling_path=None, report_id=None, prior_personal=False,
    )
    assert state.explanations_tried == [] and state.frustration_count == 0
    assert state.reply_language == "hi"


# ---- plain talk and responsible encouragement ----

def test_report_speak_openers_become_plain_talk():
    text = "Based on the retrieved biomarkers, your LDL is 138 mg/dL.\n- According to the available medical context, your HDL is 40 mg/dL."
    out = soften_robotic_phrases(text)
    assert out.startswith("Your LDL is 138 mg/dL.")
    assert "retrieved" not in out and "available medical context" not in out
    assert "- Your HDL is 40 mg/dL." in out


def test_the_patient_phrasing_is_spoken_to_you():
    assert soften_robotic_phrases("It is recommended that the patient avoid fried food.") == "You can avoid fried food."


def test_the_generic_referral_line_appears_at_most_once():
    text = "Eat well. Consult your healthcare provider for further evaluation.\n- Walk daily.\n- Please consult your doctor for further evaluation."
    out = soften_robotic_phrases(text)
    assert out.lower().count("for further evaluation") == 1


def test_plain_answers_are_left_alone():
    text = "Your LDL is **138 mg/dL**, above the report's range of under 100 mg/dL.\n- It can come down with steady changes."
    assert soften_robotic_phrases(text) == text
    assert drop_hype_and_blame(text) == text


def test_cheering_and_blame_are_removed_but_the_numbers_stay():
    out = drop_hype_and_blame("Congratulations! Your LDL fell from 162 to 138 mg/dL.\n- Well done on the walks.\nYou failed to eat well. It is still above range.")
    assert "162 to 138 mg/dL" in out and "still above range" in out
    assert "Congratulations" not in out and "Well done" not in out and "failed" not in out


# ---- end to end, multi turn ----

def _saved_state(conversation_id: str) -> ConversationState:
    db = SessionLocal()
    try:
        row = db.get(Conversation, conversation_id)
        return ConversationState.model_validate_json(row.conversation_state_json)
    finally:
        db.close()


def test_rewrite_turn_is_remembered_and_the_next_angle_is_new():
    first = chat("What does my ALT result mean?")
    cid = first["conversation_id"]
    second = chat("I still don't understand what you're saying", cid)
    assert second.get("answer")
    state = _saved_state(cid)
    assert state.user_tone == FRUSTRATED
    assert state.frustration_count == 1
    assert state.explanations_tried == [ANGLES[0]]
    assert len(second.get("follow_ups") or []) <= 2
    third = chat("Explain that more simply", cid)
    assert third.get("answer")
    state = _saved_state(cid)
    assert state.explanations_tried == [ANGLES[0], ANGLES[1]]
    assert state.frustration_count == 2


def test_the_rewrite_keeps_the_same_topic():
    cid = chat("What does my ALT result mean?")["conversation_id"]
    chat("Explain that more simply", cid)
    assert "alt" in _saved_state(cid).active_entities


def test_a_new_topic_resets_the_explanation_memory():
    cid = chat("What does my ALT result mean?")["conversation_id"]
    chat("I still don't understand", cid)
    chat("What is my vitamin D?", cid)
    state = _saved_state(cid)
    assert state.explanations_tried == [] and state.frustration_count == 0


def test_a_worried_question_still_answers_with_the_real_value():
    reply = chat("I'm worried, is my HbA1c high? Does that mean I have diabetes?")
    assert reply.get("answer")
    assert "you have diabetes" not in reply["answer"].lower() or "not" in reply["answer"].lower()


def test_written_follow_up_list_is_removed_because_chips_show_it():
    from app.pipeline.answer_consistency import drop_written_follow_ups

    text = "Your report points to one area.\n\n- Keep walking daily.\n\nFollow-up questions:\n\n- Which foods help?\n- What should I ask a doctor?\n"
    assert drop_written_follow_ups(text) == "Your report points to one area.\n\n- Keep walking daily."
    bold = "Answer here.\n\n**Follow-up questions**\n1. One?\n2. Two?"
    assert drop_written_follow_ups(bold) == "Answer here."
    assert drop_written_follow_ups("No list here.") == "No list here."


def test_card_duplicating_text_is_cleaned():
    from app.pipeline.answer_consistency import drop_good_news_opener, drop_rule_lines, trim_card_numbers

    assert drop_good_news_opener("- Good news: your liver looks fine.") == "- Your liver looks fine."
    assert drop_good_news_opener("Great news, your iron is steady.") == "Your iron is steady."
    assert drop_rule_lines("a\n-\n---\nb") == "a\nb"
    assert "range" not in trim_card_numbers("Vitamin D is low (range 30 to 100 ng/mL) today.")
    assert trim_card_numbers("**Vitamin D: 12 ng/mL** is low") == "**Vitamin D** is low"
