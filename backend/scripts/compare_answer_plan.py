#!/usr/bin/env python3
"""Compare answers with the adaptive answer plan off and on, on the same fictional member.

Without --live the model is a stub, so only the plan decisions and the prompt are checked.
With --live the configured model (LLM_API_KEY and friends) writes the answers and the automatic
quality checks below are scored. Read a sample of the answers yourself, the checks are a floor.

    python scripts/compare_answer_plan.py                 # plan decisions only, no model
    python scripts/compare_answer_plan.py --live          # real model, off versus on
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent))
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.core.config import settings

QUESTIONS = ROOT / "tests" / "fixtures" / "plan_eval_questions.json"
LABEL = re.compile(r"(?m)^\s*[-*]\s+(?!\*\*)[A-Z][A-Za-z']*(?: [A-Za-z']+){0,3}:\s+[^\d\s]")
PRAISE = re.compile(r"\b(?:great|good|nice|excellent) question\b", re.I)


def _configure(database_url: str, live: bool) -> None:
    settings.app_env = "development"
    settings.database_url = database_url
    settings.health_provider = "mock"
    settings.auth_provider = "mock"
    settings.allow_mock_header_override = True
    settings.dev_auth_header = True
    settings.supershyft_database_url = ""
    settings.jev_enabled = False
    settings.answer_cache_enabled = False
    settings.health_data_cache_seconds = 0
    settings.rate_limit_requests = 100000
    settings.member_daily_token_budget = 10**9
    settings.cura_prompt_variant = "house"
    settings.cura_response_mode = "plain"
    settings.enable_llm = True
    if not live:
        from app.llm.openai_compatible import OpenAICompatibleLLMClient

        OpenAICompatibleLLMClient.complete = lambda self, messages, json_mode=False: "- stub answer."


class _Plans(logging.Handler):
    def __init__(self) -> None:
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        message = record.getMessage()
        if message.startswith("answer_plan v="):
            self.lines.append(message)


def _checks(answer: str, previous: str | None) -> dict[str, bool]:
    lines = [ln for ln in answer.strip().splitlines() if ln.strip()]
    first = lines[0] if lines else ""
    opener = bool(lines) and not first.lstrip().startswith(("-", "*", "#")) and len(first.split()) <= 25
    sentences = {s.strip().lower() for s in re.split(r"(?<=[.!?])\s+", answer) if len(s.split()) > 5}
    before = {s.strip().lower() for s in re.split(r"(?<=[.!?])\s+", previous or "") if len(s.split()) > 5}
    return {
        "nonempty": bool(answer.strip()),
        "friendly_opener": opener,
        "no_bullet_labels": not LABEL.search(answer),
        "no_praise_opener": not PRAISE.search(answer[:160]),
        "no_dashes": "—" not in answer and "–" not in answer,
        "no_repeat_of_previous": not (previous and sentences and len(sentences & before) / len(sentences) > 0.4),
        "under_220_words": len(answer.split()) <= 220,
    }


def _ask(client, handler, message, conversation_id=None):
    handler.lines.clear()
    body = {"message": message}
    if conversation_id:
        body["conversation_id"] = conversation_id
    payload = client.post("/api/v1/chat", headers={"X-Cura-User-Id": "demo-user-001"}, json=body).json()
    return payload, (handler.lines[-1] if handler.lines else "")


def run(mode: str, questions: dict, live: bool) -> list[dict]:
    settings.answer_plan_mode = mode
    handler = _Plans()
    logging.getLogger("cura.answer_plan").addHandler(handler)
    logging.getLogger("cura.answer_plan").setLevel(logging.INFO)
    client = TestClient(__import__("app.main", fromlist=["app"]).app)
    rows: list[dict] = []
    for text in questions["single"]:
        payload, plan = _ask(client, handler, text)
        rows.append({"turns": [text], "kind": "single", "answer": payload.get("answer", ""), "plan": plan, "checks": _checks(payload.get("answer", ""), None)})
    for chain in questions["chains"]:
        previous, conversation_id = None, None
        for text in chain:
            payload, plan = _ask(client, handler, text, conversation_id)
            conversation_id = payload.get("conversation_id")
            answer = payload.get("answer", "")
            rows.append({"turns": [text], "kind": "chain", "answer": answer, "plan": plan, "checks": _checks(answer, previous)})
            previous = answer
    logging.getLogger("cura.answer_plan").removeHandler(handler)
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true", help="use the configured model")
    parser.add_argument("--out", default="plan_comparison")
    args = parser.parse_args()
    questions = json.loads(QUESTIONS.read_text())
    with tempfile.TemporaryDirectory() as tmp:
        _configure(f"sqlite:///{tmp}/cmp.db", args.live)
        results = {mode: run(mode, questions, args.live) for mode in ("off", "on")}
    out = Path(args.out)
    out.with_suffix(".json").write_text(json.dumps(results, indent=1, ensure_ascii=False))
    lines = ["# Answer plan comparison", "", f"Model: {'live' if args.live else 'stub (plan decisions only)'}", ""]
    if args.live:
        names = list(results["on"][0]["checks"])
        lines += ["| check | off | on |", "|---|---|---|"]
        for name in names:
            off = sum(r["checks"][name] for r in results["off"])
            on = sum(r["checks"][name] for r in results["on"])
            lines.append(f"| {name} | {off}/{len(results['off'])} | {on}/{len(results['on'])} |")
        lines.append("")
    lines += ["## Plan chosen per question (mode on)", "", "| question | plan |", "|---|---|"]
    for row in results["on"]:
        plan = row["plan"].replace("answer_plan v=1 ", "") or "none"
        lines.append(f"| {row['turns'][0][:70]} | {plan} |")
    if args.live:
        lines += ["", "## Answers side by side"]
        for off, on in zip(results["off"], results["on"]):
            lines += ["", f"### {off['turns'][0]}", "**off**", "", off["answer"], "", "**on**", "", on["answer"]]
    out.with_suffix(".md").write_text("\n".join(lines))
    print(f"wrote {out.with_suffix('.md')} and {out.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
