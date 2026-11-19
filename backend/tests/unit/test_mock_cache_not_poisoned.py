"""A question must not change what the next question can see.

The provider cache stores one unfiltered load per member. A provider that cached a slice
shaped by the first question made the next question say "I don't see Vitamin D".
"""
from fastapi.testclient import TestClient

from app.main import app

H = {"X-Cura-User-Id": "demo-user-001"}
client = TestClient(app)


def _ask(message):
    return client.post("/api/v1/chat", headers=H, json={"message": message}).json()["answer"]


def test_an_earlier_question_does_not_hide_a_later_marker():
    assert "HbA1c" in _ask("What is my HbA1c?")
    assert "12.6" in _ask("What is my latest Vitamin D?")
    assert "HbA1c" in _ask("What is my HbA1c?")


def test_mock_providers_cache_the_unfiltered_load():
    from app.auth.models import AuthenticatedPrincipal
    from app.pipeline.query_planner import build_query_plan
    from integrations.mock.blood_provider import MockBloodProvider

    provider = MockBloodProvider()
    me = AuthenticatedPrincipal(subject_id="demo-user-001")
    full = provider.load_for_cache(me, "latest")
    assert any(m.key for report in full for m in report.markers)
    narrow = provider.apply_plan(full, build_query_plan("What is my HbA1c?"))
    wide = provider.apply_plan(full, build_query_plan("What is my latest Vitamin D?"))
    assert {m.key for r in narrow for m in r.markers} != {m.key for r in wide for m in r.markers}
    assert provider.load_for_cache(me, "latest") == full
