"""Measure real provider prompt-cache hits and cost. Needs a model key, so run it where OPENROUTER_API_KEY is set.

    python scripts/measure_prompt_cache.py --live                       # baseline: caching fields off
    python scripts/measure_prompt_cache.py --live --cache-key           # OpenAI prompt_cache_key on
    python scripts/measure_prompt_cache.py --live --gemini-cache-control

Each question is sent twice, in two rounds. Round 1 is cold, round 2 shows what the provider reused.
Without --live a stub model answers and the token numbers are empty, so only the plumbing is checked.
Writes prompt_cache_<label>.json and prints a table. Only token counts and costs are stored: no prompts, no answers.
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import compare_answer_plan as base  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.llm import prompt_cache  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--cache-key", action="store_true")
    parser.add_argument("--gemini-cache-control", action="store_true")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--label", default="")
    args = parser.parse_args()
    label = args.label or ("keyed" if args.cache_key else "gemini_cc" if args.gemini_cache_control else "baseline")

    base._configure(f"sqlite:///{tempfile.mkdtemp()}/m.db", args.live)
    settings.llm_prompt_cache_key = args.cache_key
    settings.llm_gemini_cache_control = args.gemini_cache_control
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    questions = json.loads((Path(__file__).resolve().parents[1] / "tests/fixtures/plan_eval_questions.json").read_text())["single"][: args.limit]
    rounds: dict[int, list[dict]] = {1: [], 2: []}
    for round_no in (1, 2):
        for text in questions:
            before = len(prompt_cache.RECENT)
            client.post("/api/v1/chat", headers={"X-Cura-User-Id": "demo-user-001"}, json={"message": text})
            rounds[round_no].extend(list(prompt_cache.RECENT)[before:])
    report = {"label": label, "rounds": {}}
    print(f"\n== {label} ==")
    for round_no, rows in rounds.items():
        by_model: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_model[row["model"]].append(row)
        print(f"round {round_no}: {prompt_cache.summary(rows)}")
        report["rounds"][round_no] = {"all": prompt_cache.summary(rows), "by_model": {m: prompt_cache.summary(r) for m, r in by_model.items()}}
        for model, model_rows in by_model.items():
            print(f"   {model}: {prompt_cache.summary(model_rows)}")
    Path(f"prompt_cache_{label}.json").write_text(json.dumps(report, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
