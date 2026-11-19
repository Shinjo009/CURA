import pytest

from app.core.config import settings
from app.core.errors import LLMUnavailableError
from app.llm.openrouter_policy import OpenRouterPolicy

MODEL = "deepseek/deepseek-v4.1-flash"


@pytest.fixture()
def policy(monkeypatch):
    monkeypatch.setattr(settings, "cura_openrouter_allowed_providers", "openai,google,anthropic,typesafe,deepseek")
    monkeypatch.setattr(settings, "personal_health_privacy_profile", "safety_retention")
    monkeypatch.setattr(settings, "personal_health_approved_models", f"{MODEL},openai/gpt-5.6-luna")
    monkeypatch.setattr(settings, "llm_allowed_models", f"{MODEL},openai/gpt-5.6-luna")
    return OpenRouterPolicy.load()


def test_personal_call_to_open_weight_model_needs_approved_hosts(policy, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model_hosts", "")
    with pytest.raises(LLMUnavailableError, match="approved host"):
        policy.provider_preferences(MODEL, personal_health=True)


def test_hosts_are_pinned_with_no_fallback(policy, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model_hosts", f"{MODEL}=DeepInfra|Together;other/m=X")
    prefs = policy.provider_preferences(MODEL, personal_health=True)
    assert prefs["only"] == ["DeepInfra", "Together"] and prefs["allow_fallbacks"] is False
    assert prefs["data_collection"] == "deny"


def test_other_models_are_unchanged(policy, monkeypatch):
    monkeypatch.setattr(settings, "openrouter_model_hosts", f"{MODEL}=DeepInfra")
    assert "only" not in policy.provider_preferences("openai/gpt-5.6-luna", personal_health=True)


def test_deepseek_is_refused_unless_its_vendor_is_allowed(monkeypatch):
    monkeypatch.setattr(settings, "llm_allowed_models", MODEL)
    monkeypatch.setattr(settings, "cura_openrouter_allowed_providers", "openai,google,anthropic,typesafe")
    with pytest.raises(LLMUnavailableError):
        OpenRouterPolicy.load().assert_model(MODEL)
