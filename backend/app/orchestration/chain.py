"""The chat turn as a LangChain (langchain-core) sequence: execute, shape, finalize, persist.

Why this is a thin wrapper and not a rewrite
  * The four steps are the stages ChatService.chat already had. Each step calls the same method the
    native path calls, so there is one copy of the logic and the answers are identical (tests compare both).
  * The model is still called through CURA's own client, so the privacy policy, approved model list,
    circuit breaker, prompt-cache fields and fallbacks are unchanged. LangChain never talks to a model.
  * No retries here. A chat turn writes to the database, so repeating a step could duplicate a message.
    Timeouts and fallbacks stay where they were (TimeBudget and the model tiers).
  * No tracing. The state holds a member's health data, so LangSmith and every other callback are
    switched off, and the tests check that they stay off.
"""
from __future__ import annotations

import logging
import os
from typing import Any

logger = logging.getLogger("cura.orchestration")

_TRACING_ENV = ("LANGSMITH_TRACING", "LANGCHAIN_TRACING_V2", "LANGCHAIN_TRACING", "LANGSMITH_TRACING_V2")
_CHAIN = None


def disable_tracing() -> None:
    for name in _TRACING_ENV:
        os.environ[name] = "false"
    for name in ("LANGSMITH_API_KEY", "LANGCHAIN_API_KEY"):
        os.environ.pop(name, None)


def langchain_available() -> bool:
    try:
        import langchain_core  # noqa: F401
    except Exception:  # noqa: BLE001
        return False
    return True


def build_chain():
    """execute | shape | finalize | persist. Built once; the state dict carries everything per turn."""
    from langchain_core.runnables import RunnableLambda

    disable_tracing()

    def execute(state: dict[str, Any]) -> dict[str, Any]:
        state["response"] = state["service"]._step_execute(state["principal"], state["payload"], state["request_id"], state["eval_turn"])
        return state

    def shape(state: dict[str, Any]) -> dict[str, Any]:
        state["response"] = state["service"]._step_shape(state["response"], state["request_id"], state["eval_turn"])
        return state

    def finalize(state: dict[str, Any]) -> dict[str, Any]:
        state["response"] = state["service"]._step_finalize(state["response"], state["payload"], state["eval_turn"])
        return state

    def persist(state: dict[str, Any]) -> dict[str, Any]:
        state["response"] = state["service"]._step_persist(state["response"], state["eval_turn"], state["request_perf"])
        return state

    steps = [
        RunnableLambda(execute, name="cura_execute"),
        RunnableLambda(shape, name="cura_shape"),
        RunnableLambda(finalize, name="cura_finalize"),
        RunnableLambda(persist, name="cura_persist"),
    ]
    chain = steps[0]
    for step in steps[1:]:
        chain = chain | step
    return chain


def run_chat_chain(service, principal, payload, request_id: str, eval_turn: dict, request_perf) -> Any:
    global _CHAIN
    if _CHAIN is None:
        _CHAIN = build_chain()
    state = {
        "service": service,
        "principal": principal,
        "payload": payload,
        "request_id": request_id,
        "eval_turn": eval_turn,
        "request_perf": request_perf,
    }
    # callbacks=[] and no tags: nothing observes the state, which holds a member's results.
    result = _CHAIN.invoke(state, config={"callbacks": [], "tags": [], "metadata": {}})
    return result["response"]
