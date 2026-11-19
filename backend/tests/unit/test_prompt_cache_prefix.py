"""The static instruction prefix is shared; personal context never enters it."""
import json

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.llm import prompt_cache
from app.llm.openai_compatible import OpenAICompatibleLLMClient
from app.main import app

client = TestClient(app)


@pytest.fixture()
def capture(monkeypatch):
    monkeypatch.setattr(settings, "cura_prompt_variant", "house")
    monkeypatch.setattr(settings, "answer_plan_mode", "on")
    seen = []

    def fake(self, messages, json_mode=False):
        seen.append(([dict(m) for m in messages], prompt_cache.current_boundary()))
        return "- stub."

    monkeypatch.setattr(OpenAICompatibleLLMClient, "complete", fake)
    monkeypatch.setattr(settings, "enable_llm", True)
    return seen


def ask(user, text):
    return client.post("/api/v1/chat", headers={"X-Cura-User-Id": user}, json={"message": text}).json()


def static_of(entry):
    messages, boundary = entry
    system = next(m["content"] for m in messages if m["role"] == "system")
    return system[: boundary.static_chars], boundary


def test_two_users_two_questions_share_one_static_prefix(capture):
    ask("demo-user-001", "What is my LDL?")
    ask("demo-user-002", "What causes vitamin D deficiency?")
    entries = [e for e in capture if e[1] is not None]
    assert len(entries) >= 2
    (a, ba), (b, bb) = static_of(entries[0]), static_of(entries[1])
    assert ba.shape == bb.shape == "narrow"
    assert a == b and ba.prefix_id == bb.prefix_id


def test_personal_values_stay_out_of_the_static_prefix_and_the_system_message(capture):
    ask("demo-user-001", "What is my LDL?")
    messages, boundary = capture[-1]
    system = next(m["content"] for m in messages if m["role"] == "system")
    user = next(m["content"] for m in messages if m["role"] == "user")
    for value in ("138.0", "12.6", "154.0"):
        assert value not in system
    assert "138.0" in user
    assert "demo-user" not in system


def test_changing_question_report_or_history_does_not_change_the_prefix(capture):
    ask("demo-user-001", "What is my LDL?")
    first = static_of(capture[-1])
    ask("demo-user-001", "Why is my vitamin D low?")
    second = static_of(capture[-1])
    ask("demo-user-002", "What is my LDL?")
    third = static_of(capture[-1])
    assert first[0] == second[0] == third[0]


def test_static_prefix_is_deterministic_text():
    from app.pipeline.prompt_modules import HOUSE_CORE, WARM_VOICE, _NO_FIELD_NAMES

    assert "demo" not in HOUSE_CORE.lower()
    assert HOUSE_CORE.strip() and WARM_VOICE and _NO_FIELD_NAMES


def test_provider_fields_are_provider_specific(monkeypatch):
    monkeypatch.setattr(settings, "llm_prompt_cache_key", True)
    monkeypatch.setattr(settings, "llm_gemini_cache_control", True)
    prompt_cache.set_boundary("STATIC", "narrow")
    messages = [{"role": "system", "content": "STATIC then dynamic"}, {"role": "user", "content": "q"}]
    openai = prompt_cache.apply_cache_fields({"messages": messages}, "openai/gpt-5-mini")
    assert openai["prompt_cache_key"].startswith("cura-") and "demo" not in openai["prompt_cache_key"]
    assert openai["messages"] == messages
    gemini = prompt_cache.apply_cache_fields({"messages": [dict(m) for m in messages]}, "google/gemini-3.8-flash")
    parts = gemini["messages"][0]["content"]
    assert parts[0]["text"] == "STATIC" and parts[0]["cache_control"] == {"type": "ephemeral"}
    assert parts[0]["text"] + parts[1]["text"] == "STATIC then dynamic"
    assert "prompt_cache_key" not in gemini


def test_cache_fields_are_off_by_default():
    prompt_cache.set_boundary("STATIC", "narrow")
    payload = prompt_cache.apply_cache_fields({"messages": [{"role": "system", "content": "STATIC x"}]}, "openai/gpt-5-mini")
    assert "prompt_cache_key" not in payload


def test_observability_row_has_the_required_fields():
    prompt_cache.set_boundary("STATIC", "narrow")
    row = prompt_cache.record(
        model="openai/gpt-5-mini", upstream_provider="OpenAI",
        usage={"usage_reported": True, "input_tokens": 3000, "cached_tokens": 2000, "cache_write_tokens": 0, "provider_cost": 0.001},
        latency_ms=1200,
    )
    for key in ("model", "provider", "prompt_version", "input_tokens", "cached_tokens", "cache_write_tokens",
                "cache_hit_rate", "estimated_input_cost_usd", "latency_ms"):
        assert key in row
    assert row["cache_hit_rate"] == round(2000 / 3000, 3)
    assert "demo" not in json.dumps(row)
