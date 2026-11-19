"""Gemini is tried once, last, only after every tier model failed."""
from types import SimpleNamespace

import pytest

from app.contracts.common import AnswerModelTier
from app.core.config import settings
from app.core.errors import LLMUnavailableError
from app.llm.models import LLMStructuredOutput
from app.llm.openai_compatible import OpenAICompatibleLLMClient
from app.llm.registry import fallback_tiers, safety_net_model
from app.pipeline.reasoning import ReasoningService
from app.pipeline.service import ChatService

PLAN = SimpleNamespace(answer_model_tier=AnswerModelTier.standard_medical, complexity_score=5, needs_personal_data=False)


@pytest.fixture()
def calls(monkeypatch):
    seen = []

    def make(fail_for):
        def fake(self, messages):
            seen.append(self.model)
            if any(self.model.startswith(prefix) for prefix in fail_for):
                raise LLMUnavailableError("down")
            return LLMStructuredOutput(answer="- ok.")
        monkeypatch.setattr(OpenAICompatibleLLMClient, "complete_structured", fake)
        return seen
    monkeypatch.setattr(settings, "enable_llm", True)
    monkeypatch.setattr(settings, "personal_health_privacy_profile", "safety_retention")
    return make


def _service_stub():
    stub = SimpleNamespace(_stream_cb=None)
    stub._try_safety_net = lambda *args: ChatService._try_safety_net(stub, *args)
    return stub


@pytest.mark.parametrize("which", ["service", "reasoning"])
def test_gemini_answers_only_when_the_openai_models_fail(calls, which):
    seen = calls(fail_for=("openai/",))
    dummy = _service_stub()
    func = (ChatService if which == "service" else ReasoningService)._complete_answer
    result, client, tier, fallback = func(dummy, [{"role": "system", "content": "s"}, {"role": "user", "content": "u"}], PLAN)
    assert client.model == "google/gemini-3.8-flash" and fallback is True
    assert seen[-1] == "google/gemini-3.8-flash" and seen.count("google/gemini-3.8-flash") == 1
    assert all(m.startswith("openai/") for m in seen[:-1])


@pytest.mark.parametrize("which", ["service", "reasoning"])
def test_gemini_is_not_called_when_a_tier_model_works(calls, which):
    seen = calls(fail_for=())
    dummy = _service_stub()
    func = (ChatService if which == "service" else ReasoningService)._complete_answer
    func(dummy, [{"role": "user", "content": "u"}], PLAN)
    assert seen == ["openai/gpt-5-mini"]


def test_all_models_failing_still_raises(calls):
    calls(fail_for=("openai/", "google/"))
    with pytest.raises(LLMUnavailableError):
        ChatService._complete_answer(_service_stub(), [{"role": "user", "content": "u"}], PLAN)


def test_safety_net_can_be_turned_off_and_is_skipped_when_already_tried(monkeypatch):
    assert safety_net_model(set()) == "google/gemini-3.8-flash"
    assert safety_net_model({"google/gemini-3.8-flash"}) is None
    monkeypatch.setattr(settings, "answer_model_safety_net", "")
    assert safety_net_model(set()) is None
