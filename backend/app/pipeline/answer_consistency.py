"""Small deterministic checks that keep an answer consistent with the facts it was given.

Each one changes a number, a name or a stock phrase and nothing else. None adds a medical claim.
"""

from __future__ import annotations

import re

from app.pipeline.gap_words import how_far

_RAISED = {"critical", "very high", "high", "elevated", "moderate", "medium"}

# "8 assessment areas and 7 are raised", "covers 8 areas, with 5 raised", "looked at 8 assessment areas and 5 were raised"
_AREA_COUNT = re.compile(
    r"(?P<total>\d+)(?P<mid>\s+(?:assessment\s+)?areas?\b[^.;\n]{0,25}?\b)(?P<raised>\d+)(?P<tail>\s+(?:of\s+them\s+)?(?:was|were|are|is)?\s*raised)",
    re.I,
)
_AREA_OF = re.compile(
    r"(?P<raised>\d+)(?P<mid>\s+of\s+(?:your\s+|the\s+)?)(?P<total>\d+)(?P<tail>\s+(?:assessment\s+)?areas?\b[^.;\n]{0,20}?\braised)",
    re.I,
)


def bio_ai_counts(context) -> tuple[int, int] | None:
    risks = list(getattr(context, "bio_ai_risks", None) or [])
    if not risks:
        return None
    raised = sum(1 for risk in risks if (getattr(risk, "status", None) or "").lower() in _RAISED)
    return len(risks), raised


def fix_bio_ai_counts(text: str, context) -> str:
    """The number of assessment areas and raised areas is a count from the report, never the model's tally."""
    counts = bio_ai_counts(context)
    if not text or counts is None:
        return text
    total, raised = counts

    def count_form(match: re.Match) -> str:
        return f"{total}{match.group('mid')}{raised}{match.group('tail')}"

    def of_form(match: re.Match) -> str:
        return f"{raised}{match.group('mid')}{total}{match.group('tail')}"

    return _AREA_OF.sub(of_form, _AREA_COUNT.sub(count_form, text))


_CLOSER = re.compile(
    r"^\W*(?:small|little|tiny)\W{0,3}(?:steady|careful|consistent|simple|regular)\b[^.!?\n]*[.!?]?\s*$",
    re.I,
)


def drop_stock_closer(text: str) -> str:
    """"Small, steady steps add up" ended 4 answers in 10. It carries no fact, so the stock line goes."""
    if not text:
        return text
    lines: list[str] = []
    for line in text.split("\n"):
        marker = re.match(r"^(\s*[-*]\s+)", line)
        body = line[marker.end():] if marker else line
        parts = re.split(r"(?<=[.!?])\s+", body)
        kept = [part for part in parts if not _CLOSER.match(part)]
        if len(kept) == len(parts):
            lines.append(line)
            continue
        joined = " ".join(kept).strip()
        if joined:
            lines.append((marker.group(1) if marker else "") + joined)
    return "\n".join(lines)


_REFERRAL = re.compile(
    r"\b(?:doctor|clinician|physician)\b.*\b(?:see|show|discuss|arrange|visit|speak|talk|consult|review)\b"
    r"|\b(?:see|show|discuss|arrange|visit|speak|talk|consult|review)\b.*\b(?:doctor|clinician|physician)\b",
    re.I,
)


def collapse_referrals(text: str) -> str:
    """A short answer asks the person to see a doctor once, not twice in two bullets."""
    if not text or "\n#" in text or text.lstrip().startswith("#"):
        return text
    seen = False
    out: list[str] = []
    for line in text.split("\n"):
        marker = re.match(r"^(\s*[-*]\s+)", line)
        body = line[marker.end():] if marker else line
        parts = re.split(r"(?<=[.!?])\s+", body)
        kept: list[str] = []
        for part in parts:
            if _REFERRAL.search(part):
                if seen:
                    continue
                seen = True
            kept.append(part)
        joined = " ".join(kept).strip()
        if kept and joined:
            out.append((marker.group(1) if marker else "") + joined)
        elif not parts or not body.strip():
            out.append(line)
    return "\n".join(out)


_BOLD_LABEL = re.compile(r"\*\*(?P<name>[^*:\n]{2,40}):\s*(?P<value>[^*\n]+?)\*\*")


def drop_label_echo(text: str) -> str:
    """"Your creatinine is **Creatinine: 0.92 mg/dL**" says the name twice. Keep the bold value."""
    if not text:
        return text

    def fix(match: re.Match) -> str:
        name = match.group("name").strip().lower()
        before = text[max(0, match.start() - 70): match.start()].lower()
        if name and name in before and not re.search(r"[.!?]\s*$", before.strip()[-1:] or ""):
            return f"**{match.group('value').strip()}**"
        return match.group(0)

    return _BOLD_LABEL.sub(fix, text)


def blood_half_for_ambiguity(context, limit: int = 3) -> str:
    """When a blood and Bio-AI question stalls on which Bio-AI report, say what the blood report shows right away."""
    rows = []
    for marker in getattr(context, "markers", None) or []:
        word = how_far(getattr(marker, "value", None), getattr(marker, "reference_low", None), getattr(marker, "reference_high", None))
        if not word:
            continue
        low, high, value = marker.reference_low, marker.reference_high, marker.value
        above = high is not None and value > high
        limit_value = high if above else low
        share = abs(value - limit_value) / abs(limit_value) if limit_value else 0
        rows.append((share, marker, word, above))
    if not rows:
        return ""
    rows.sort(key=lambda item: -item[0])
    lines = []
    for _, marker, word, above in rows[:limit]:
        unit = f" {marker.unit}" if getattr(marker, "unit", None) else ""
        direction = "above" if above else "below"
        lo = f"{marker.reference_low:g}" if marker.reference_low is not None else None
        hi = f"{marker.reference_high:g}" if marker.reference_high is not None else None
        rng = f"{lo} to {hi}{unit}" if lo is not None and hi is not None else (f"under {hi}{unit}" if hi is not None else f"over {lo}{unit}")
        lines.append(f"- **{marker.name}: {marker.value:g}{unit}** is {word} {direction} the range on your report ({rng}).")
    return "From your blood report, these stand out most:\n" + "\n".join(lines)
