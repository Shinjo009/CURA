"""Provider-native prompt caching: boundaries, request fields and observability.

CURA keeps NO application-level prompt cache. Nothing here stores a prompt, an answer, a report or a
conversation. The provider (through OpenRouter) caches a repeated request prefix on its side, under the
same data-collection settings as every other call. This module only
  * remembers where the static instructions end (a length, never the text),
  * adds the provider-specific request fields that help the provider reuse that prefix, and
  * records numbers (tokens, hit rate, cost estimate, latency) for each call.

The prefix is static instruction text only. Evidence, reports, scores, history and the question come after it.
"""

from __future__ import annotations

import hashlib
import json
import logging
from collections import deque
from contextvars import ContextVar
from dataclasses import dataclass

from app.core.config import settings

logger = logging.getLogger("cura.prompt_cache")

RECENT: deque = deque(maxlen=1000)  # numbers only: no prompt text, no patient data


@dataclass(frozen=True)
class Boundary:
    static_chars: int  # the system message starts with this many characters of static text
    prefix_id: str  # hash of the static text; changes whenever the instructions change
    shape: str  # "narrow" or "wide": which static variant this request used


_BOUNDARY: ContextVar[Boundary | None] = ContextVar("cura_prompt_boundary", default=None)


def set_boundary(static_text: str, shape: str) -> Boundary:
    boundary = Boundary(len(static_text), hashlib.sha256(static_text.encode("utf-8")).hexdigest()[:10], shape)
    _BOUNDARY.set(boundary)
    return boundary


def current_boundary() -> Boundary | None:
    return _BOUNDARY.get()


def _is_openai(model: str) -> bool:
    return (model or "").startswith("openai/")


def _is_gemini(model: str) -> bool:
    return (model or "").startswith("google/")


def apply_cache_fields(payload: dict, model: str) -> dict:
    """Add the fields each provider needs. Providers do not share one API, so each is handled on its own.

    OpenAI: caching is automatic for a prompt of 1,024 tokens or more. A shared, non-identifying
      prompt_cache_key can improve routing to the same cache (off by default until measured).
    Gemini: implicit caching, or an explicit cache_control breakpoint on a content block (off by default).
    Anthropic is not in the routing today, so nothing is sent for it.
    """
    boundary = current_boundary()
    if boundary is None:
        return payload
    if _is_openai(model) and settings.llm_prompt_cache_key:
        # Never a user, member or conversation id: the key is shared by everyone on this static prefix.
        payload["prompt_cache_key"] = f"cura-{boundary.prefix_id}-{boundary.shape}"
    if _is_gemini(model) and settings.llm_gemini_cache_control:
        messages = payload.get("messages") or []
        if messages and messages[0].get("role") == "system" and isinstance(messages[0].get("content"), str):
            text = messages[0]["content"]
            if 0 < boundary.static_chars < len(text):
                payload["messages"] = [
                    {
                        "role": "system",
                        "content": [
                            {"type": "text", "text": text[: boundary.static_chars], "cache_control": {"type": "ephemeral"}},
                            {"type": "text", "text": text[boundary.static_chars:]},
                        ],
                    },
                    *messages[1:],
                ]
    return payload


def _input_price(model: str) -> float | None:
    from app.llm.registry import model_pricing

    price = model_pricing().get(model)
    return price.input_per_1m if price else None


def record(*, model: str, upstream_provider: str | None, usage: dict, latency_ms: int) -> dict | None:
    """One row per call. The cost is an ESTIMATE from the configured price and read factor; provider_cost is the bill."""
    boundary = current_boundary()
    if not usage or not usage.get("usage_reported"):
        return None
    total = int(usage.get("input_tokens") or 0)
    cached = int(usage.get("cached_tokens") or 0)
    written = int(usage.get("cache_write_tokens") or 0)
    price = _input_price(model)
    estimate = None
    if price is not None:
        uncached = max(total - cached - written, 0)
        estimate = round(
            (uncached + written * settings.llm_cache_write_factor + cached * settings.llm_cache_read_factor) * price / 1_000_000,
            8,
        )
    row = {
        "model": model,
        "provider": upstream_provider or settings.resolved_llm_provider(),
        "prompt_version": boundary.prefix_id if boundary else None,
        "shape": boundary.shape if boundary else None,
        "input_tokens": total,
        "cached_tokens": cached,
        "cache_write_tokens": written,
        "cache_hit_rate": round(cached / total, 3) if total else 0.0,
        "estimated_input_cost_usd": estimate,
        "provider_cost_usd": usage.get("provider_cost"),
        "latency_ms": latency_ms,
    }
    RECENT.append(row)
    logger.info("prompt_cache %s", json.dumps(row, sort_keys=True))
    return row


def summary(rows: list[dict] | None = None) -> dict:
    rows = list(RECENT if rows is None else rows)
    total = sum(r["input_tokens"] for r in rows)
    cached = sum(r["cached_tokens"] for r in rows)
    return {
        "calls": len(rows),
        "input_tokens": total,
        "cached_tokens": cached,
        "cache_hit_rate": round(cached / total, 3) if total else 0.0,
        "estimated_input_cost_usd": round(sum(r["estimated_input_cost_usd"] or 0 for r in rows), 6),
        "provider_cost_usd": round(sum(r["provider_cost_usd"] or 0 for r in rows), 6),
        "avg_latency_ms": int(sum(r["latency_ms"] for r in rows) / len(rows)) if rows else 0,
    }
