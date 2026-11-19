# Orchestration: LangChain around the chat turn

`ChatService.chat` runs four steps: execute (the whole pipeline), shape (response mode and semantic blocks), finalize (last clean-up pass) and persist (save and timing). With `CURA_ORCHESTRATION=langchain` (the default) they run as a `langchain-core` sequence in `app/orchestration/chain.py`. With `CURA_ORCHESTRATION=native`, or if langchain-core is not installed, the same four methods run in order. The answers are identical.

Rules that keep it safe
- LangChain never calls a model. Model calls still go through CURA's client (approved models, privacy profile, circuit breaker, prompt cache fields, tier fallbacks).
- No retries in the chain: a turn writes to the database, so repeating a step could duplicate a message. Timeouts stay with `TimeBudget`.
- No tracing: LangSmith variables are forced off, the API key is removed and no callbacks are attached, because the state holds a member's results.
- Errors propagate unchanged.

Parity: `tests/unit/test_langchain_orchestration.py` compares both engines on the evaluation questions and conversation chains (`CURA_FULL_PARITY=1` for all 57). Overhead measured at about 3 ms per request.
