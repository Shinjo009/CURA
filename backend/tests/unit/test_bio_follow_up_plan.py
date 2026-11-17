from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
HEADERS = {"X-Cura-User-Id": "demo-user-001"}


def test_follow_up_after_bio_ai_question_does_not_crash():
    first = client.post("/api/v1/chat", headers=HEADERS, json={"message": "Explain my Bio-AI report"})
    assert first.status_code == 200
    cid = first.json()["conversation_id"]
    for message in ("What about my metabolic score?", "Give me the detailed version"):
        follow = client.post(
            "/api/v1/chat", headers=HEADERS, json={"message": message, "conversation_id": cid}
        )
        assert follow.status_code == 200
