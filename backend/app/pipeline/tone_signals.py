"""Read how the person is feeling and what shape of answer they want. Deterministic, no model call.

The result becomes two or three short lines in the answer prompt. It never changes which facts are
used, only how they are said. A wrong guess costs a slightly different tone, never a wrong number.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.pipeline.personalization_context import _DEEP_RE, _QUICK_RE

WORRIED = "worried"
FRUSTRATED = "frustrated"
CURIOUS = "curious"
QUICK = "quick"
DETAILED = "detailed"
NEUTRAL = "neutral"

_WORRIED_RE = re.compile(
    r"\b(worr(?:y|ied|ying)|scared|afraid|anxious|anxiety|nervous|panic(?:king)?|frightened|"
    r"should i be (?:worried|concerned)|does (?:that|this|it) mean i have|am i going to|"
    r"is it serious|how serious|is (?:it|this|that) dangerous|will i die|ghabra\w*|dar lag\w*|chinta|tension)\b"
    r"|चिंता|घबरा|डर",
    re.I,
)
_FRUSTRATED_RE = re.compile(
    r"\b(still (?:don'?t|do not|can'?t|cannot) (?:understand|get|follow)|"
    r"(?:don'?t|do not|didn'?t|did not|can'?t|cannot) (?:really )?(?:understand|get it|follow)|"
    r"doesn'?t make sense|makes? no sense|too (?:complicated|technical|confusing|long)|so confusing|"
    r"i'?m (?:lost|confused)|what do you mean|samajh (?:nahi|nhi)|samjha nahi|samajh nahi aaya)\b"
    r"|समझ नहीं",
    re.I,
)
_REWRITE_RE = re.compile(
    r"\b(simpl(?:er|y)|rephrase|reword|another way|different(?:ly| way)|dumb it down|easier to understand|"
    r"in simple (?:words|terms|language)|plain (?:english|words)|explain (?:it|that|this) (?:more )?(?:simply|clearly)|"
    r"say (?:that|it) again|once more|asaan|aasan|seedha)\b",
    re.I,
)
_CURIOUS_RE = re.compile(
    r"^\s*(?:why (?:does|do|is it that)|how (?:does|do|is)|what (?:causes|makes|happens)|"
    r"what'?s the (?:reason|science)|kaise|kyun)\b",
    re.I,
)
_DIRECT_RE = re.compile(
    r"^\s*(?:is|are|was|were|am)\s+(?:my|the|this)\b[^?]{0,60}\b(normal|ok|okay|fine|high|low|in range|healthy)\b",
    re.I,
)

# Angles for explaining the same facts again. Each rewrite uses the next one not tried yet.
ANGLES = (
    "an everyday comparison, then the result in one plain sentence",
    "tiny steps, one idea at a time, with the person's own number placed in the middle",
    "one idea only, as short as you can make it, no new terms",
)


@dataclass(frozen=True)
class ToneSignals:
    tone: str = NEUTRAL
    wants_rewrite: bool = False


def is_rewrite_request(message: str, *, mentions_topic: bool = False) -> bool:
    """A short message asking for the previous answer in a different way, with no new topic of its own."""
    text = (message or "").strip()
    if not text or mentions_topic or len(text.split()) > 14:
        return False
    return bool(_FRUSTRATED_RE.search(text) or _REWRITE_RE.search(text))


def detect_tone(message: str, *, mentions_topic: bool = False) -> ToneSignals:
    text = message or ""
    rewrite = is_rewrite_request(text, mentions_topic=mentions_topic)
    if _FRUSTRATED_RE.search(text):
        return ToneSignals(FRUSTRATED, rewrite)
    if _WORRIED_RE.search(text):
        return ToneSignals(WORRIED, rewrite)
    if _QUICK_RE.search(text) or _DIRECT_RE.search(text):
        return ToneSignals(QUICK, rewrite)
    if _DEEP_RE.search(text) or re.search(r"\b(everything|all about)\b", text, re.I):
        return ToneSignals(DETAILED, rewrite)
    if _CURIOUS_RE.search(text):
        return ToneSignals(CURIOUS, rewrite)
    return ToneSignals(NEUTRAL, rewrite)


def pick_angle(tried: list[str] | None) -> str:
    used = set(tried or [])
    for angle in ANGLES:
        if angle not in used:
            return angle
    return ANGLES[len(used) % len(ANGLES)]


_TONE_LINES = {
    WORRIED: (
        "The person sounds worried. Open with half a sentence of calm acknowledgement, give the actual value if you have it, "
        "say plainly what is known and what is not (a screening result or a score is not a diagnosis), and state any concern once. "
        "No alarm words and no false reassurance."
    ),
    FRUSTRATED: (
        "The last explanation did not land. Do not repeat it with new wording. Open with a few warm words that take the blame "
        "on yourself, in your own varied phrasing."
    ),
    CURIOUS: (
        "The person is curious about how it works. Explain the mechanism with one everyday comparison, then stop. "
        "Do not turn it into a lecture."
    ),
    QUICK: "The person wants a quick answer. The first sentence is the answer, with the real value and its range. No extra paragraphs.",
    DETAILED: (
        "A fuller answer is welcome. Cover the related results, how they connect, what this person's own numbers say and what it "
        "means in practice, in short readable bullets."
    ),
}


def tone_brief(context) -> str:
    """Prompt lines for the tone and rewrite state held on the context. Empty for an ordinary turn."""
    lines: list[str] = []
    tone_line = _TONE_LINES.get(getattr(context, "user_tone", None) or NEUTRAL)
    if tone_line:
        lines.append(tone_line)
    previous = getattr(context, "rewrite_previous_answer", None)
    if previous:
        angle = getattr(context, "rewrite_angle", None) or ANGLES[0]
        lines.append(
            "REWRITE: explain your previous answer again, shown below, so it is easier to follow. Keep every number, unit, date "
            "and safety instruction exactly the same and add no new facts. Do not reuse its sentences or its structure. "
            f"This time use {angle}. Previous answer: \"{previous}\""
        )
    return " ".join(lines)


def follow_up_limit(tone: str | None, rewrite: bool = False) -> int:
    """A person who is lost or in a hurry gets fewer next steps, not more."""
    if rewrite or tone in {FRUSTRATED, QUICK}:
        return 2
    if tone == WORRIED:
        return 3
    return 4


def trim_follow_ups(items: list, tone: str | None, rewrite: bool = False) -> list:
    return list(items)[: follow_up_limit(tone, rewrite)]
