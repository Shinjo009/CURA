"""English pivot for localized answers (readiness plan 3.3).

The answer is generated and checked in English (grounding and safety checks stay
effective), then translated by a small fast model. The translation is used only if every
number in it matches the English answer; otherwise the member gets the checked English.
Static safety replies are localized separately in ``safety_messages``.
"""

from __future__ import annotations

import logging
import re
from collections import Counter

import httpx

from app.core.config import settings
from app.pipeline.grounding import to_ascii_digits
from app.pipeline.safety_messages import detect_safety_language

logger = logging.getLogger("cura.translation")

LANGUAGE_NAMES = {
    "hi": "Hindi (Devanagari script)",
    "hinglish": "Hinglish (Hindi written in Roman script)",
    "mr": "Marathi (Devanagari script)",
    "pa": "Punjabi (Gurmukhi script)",
    "gu": "Gujarati (Gujarati script)",
    "bn": "Bengali (Bengali script)",
}
_NUMBER = re.compile(r"\d+(?:[.,]\d+)?")


def target_language(message: str, language: str | None = None, language_mode: str | None = None) -> str:
    """The member's language: an explicit choice wins, else the script of their message."""
    if (language_mode or "auto") == "manual" and language:
        chosen = language.strip().lower()
    else:
        chosen = detect_safety_language(message)
    enabled = {item.strip().lower() for item in (settings.answer_languages or "en").split(",") if item.strip()}
    return chosen if chosen in enabled and chosen in LANGUAGE_NAMES else "en"


_ENGLISH_ASK = re.compile(r"\b(?:in|reply in|answer in|speak in|switch to) english\b|\benglish (?:me|mein|mai|please)\b", re.I)


def sticky_target_language(
    message: str, prior: str | None, language: str | None = None, language_mode: str | None = None
) -> str:
    """The reply language, kept steady across a conversation.

    A language the person wrote in stays for their next very short message ("and LDL?", "why?"), so a
    one word follow up does not flip a Hindi conversation back to English. Any real English message, or
    a request for English, is a switch. An explicit language setting always wins.
    """
    chosen = target_language(message, language, language_mode)
    if (language_mode or "auto") == "manual" or chosen != "en" or not prior or prior == "en":
        return chosen
    if _ENGLISH_ASK.search(message or "") or len((message or "").split()) > 3:
        return "en"
    enabled = {item.strip().lower() for item in (settings.answer_languages or "en").split(",") if item.strip()}
    return prior if prior in enabled and prior in LANGUAGE_NAMES else "en"


def numbers_match(source: str, translated: str) -> bool:
    def bag(text: str) -> Counter:
        return Counter(n.replace(",", ".") for n in _NUMBER.findall(to_ascii_digits(text)))

    return bag(source) == bag(translated)


def _prompt(language: str, answer: str = "") -> str:
    from app.i18n.glossary import glossary_lines

    approved = glossary_lines(answer, language)
    glossary = (
        " Use these approved local names for the terms that appear: " + "; ".join(approved) + "."
        if approved
        else ""
    )
    return (
        f"Translate the health answer into {LANGUAGE_NAMES[language]} for an Indian reader at about a "
        "grade 6 to 8 reading level. Rules: keep every number, unit, date and range exactly as written, "
        "using the same digits; keep biomarker abbreviations (HbA1c, LDL, TSH, eGFR...) unchanged; when you "
        "use a local name for a biomarker, put the English name in brackets after it; keep line breaks and "
        "bullet structure; add nothing and leave nothing out. Reply with the translation only."
        + glossary
    )


def translate_answer(answer: str, language: str, client: httpx.Client | None = None) -> tuple[str, str, list[str]]:
    """Return (text, response_language, flags). Falls back to English on any problem."""
    if language == "en" or not (answer or "").strip():
        return answer, "en", []
    from app.i18n.catalog import localize_known

    known = localize_known(answer, language)
    if known:
        # Fixed catalog text: reviewed translation, no model call.
        return known, language, []
    if not (settings.enable_llm and settings.answer_translation_enabled):
        return answer, "en", ["translation_unavailable"]
    api_key = settings.active_llm_api_key()
    model = settings.translation_model
    try:
        from app.llm.openrouter_policy import openrouter_policy

        payload = {
            "model": model,
            "messages": [{"role": "system", "content": _prompt(language, answer)}, {"role": "user", "content": answer}],
            "temperature": 0,
            "max_tokens": min(4000, 3 * max(200, len(answer) // 2)),
            "provider": openrouter_policy().provider_preferences(model, personal_health=True),
            "reasoning": {"effort": "low"},
        }
        own = client is None
        client = client or httpx.Client(timeout=settings.translation_timeout_seconds)
        try:
            response = client.post(
                f"{settings.active_llm_base_url()}/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "X-Title": settings.openrouter_app_title},
                json=payload,
                timeout=settings.translation_timeout_seconds,
            )
        finally:
            if own:
                client.close()
        response.raise_for_status()
        translated = (response.json()["choices"][0]["message"]["content"] or "").strip()
    except Exception as exc:  # noqa: BLE001 - timeout, policy refusal, bad response
        logger.warning("translation status=failed language=%s error=%s", language, type(exc).__name__)
        return answer, "en", ["translation_failed"]
    if not translated:
        return answer, "en", ["translation_failed"]
    if not numbers_match(answer, translated):
        logger.warning("translation status=rejected reason=number_mismatch language=%s", language)
        return answer, "en", ["translation_number_mismatch"]
    return translated, language, []
