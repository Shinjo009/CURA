"""Turn a Bio-AI risk explanation into structured parts.

The model writes the explanation in plain words. Everything measured (score, level, date, blood
values) is attached here from the report, so the model can never change a number.
"""

from __future__ import annotations

import re

from app.contracts.presentation import (
    ExplainerAction,
    ExplainerSection,
    PresentedFinding,
    RelatedTest,
    RiskExplanation,
    RiskScoreCard,
)

_H2 = re.compile(r"^##\s+(.+?)\s*$")
_H3 = re.compile(r"^###\s+(.+?)\s*$")
_ANY_HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")
_MORE = re.compile(r"explore|learn more|more about", re.I)
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)\s*$")
MAX_RELATED, MAX_ACTIONS, MAX_ITEMS = 3, 4, 4

# Icon ids by wording of the action. General habit vocabulary, not tied to any condition.
_ICON_WORDS = (
    ("meal", r"\b(?:eat|meals?|food|diet|dal|vegetables?|fruit|grains?|fibre|fiber|snack|cook|breakfast|lunch|dinner|portion)\b"),
    ("move", r"\b(?:walk\w*|move|exercis\w*|active|activity|steps|run\w*|yoga|stretch\w*|workout|cycl\w*|swim\w*)\b"),
    ("sleep", r"\b(?:sleep\w*|bedtime|rest\w*|night)\b"),
    ("stress", r"\b(?:stress\w*|relax\w*|breath\w*|calm|mind\w*|meditat\w*)\b"),
    ("water", r"\b(?:water|hydrat\w*|drink\w*|fluids?)\b"),
    ("test", r"\b(?:test\w*|check\w*|recheck|screen\w*|monitor\w*|track\w*)\b"),
    ("doctor", r"\b(?:doctor|physician|clinician|appointment|consult\w*)\b"),
    ("weight", r"\b(?:weight|waist)\b"),
    ("smoke", r"\b(?:smok\w*|tobacco|alcohol)\b"),
)


def action_icon(text: str) -> str:
    for icon, pattern in _ICON_WORDS:
        if re.search(pattern, text or "", re.I):
            return icon
    return "habit"


def _split_item(text: str) -> tuple[str, str]:
    m = re.match(r"\*\*(.+?)\*\*\s*[:.,]?\s*(.*)$", text)
    if m:
        return m.group(1).strip(" :").replace("**", ""), m.group(2).replace("**", "").strip()
    if ":" in text[:70]:
        a, b = (p.strip() for p in text.split(":", 1))
        return a.replace("**", ""), b.replace("**", "")
    return text.replace("**", "").strip(), ""


_NOTE = re.compile(r"left out|did not list|not listed|not supplied|no (?:specific )?(?:blood )?(?:markers?|tests?) (?:were|was|are)|section is", re.I)
_ESTIMATE = re.compile(r"estimate of (?:your )?future risk|not a diagnosis", re.I)


def _paragraphs(lines: list[str]) -> list[str]:
    """One point per bullet. A plain paragraph becomes one point. Notes about missing data and the stock estimate line are dropped."""
    out, cur = [], []
    for line in lines:
        b = _BULLET.match(line)
        if b:
            if cur:
                out.append(" ".join(cur))
                cur = []
            out.append(b.group(1))
        elif not line.strip():
            if cur:
                out.append(" ".join(cur))
                cur = []
        else:
            cur.append(line.strip())
    if cur:
        out.append(" ".join(cur))
    points = [p.replace("**", "").strip() for p in out if p.strip()]
    return [p for p in points if not _NOTE.search(p) and not _ESTIMATE.search(p)]


def score_card_for(risk) -> RiskScoreCard:
    from app.biomarkers.risk_overview import _level

    from app.biomarkers.risk_overview import _display, _registry

    code = re.sub(r"[^a-z0-9]+", "_", (risk.code or risk.name or "").lower()).strip("_")
    return RiskScoreCard(
        code=risk.code,
        name=_display(_registry(), code, risk.name).get("name", risk.name),
        score=risk.score,
        status=risk.status,
        level=_level(risk.status),
        assessed_on=str(risk.measured_at)[:10] if risk.measured_at else None,
        percentile=risk.percentile,
        lifestyle_contribution=risk.lifestyle_contribution,
        contributing_factors=list(risk.contributing_factors or []),
    )


def _marker_for(key: str, markers):
    from app.pipeline.prompt_builder import _topic_key

    wanted = _topic_key(key)
    return next((m for m in markers if _topic_key(m.key) == wanted or _topic_key(m.name) == wanted), None)


def parse_risk_explanation(text: str, *, risk, markers) -> RiskExplanation | None:
    """Return the structured explanation, or None when the answer does not follow the layout."""
    sections: list[tuple[str, list[str]]] = []
    in_more = False
    for line in (text or "").split("\n"):
        h = _ANY_HEADING.match(line)
        if h and in_more:
            sections[-1][1].append(f"### {h.group(1)}")  # every heading after "More to explore" is a sub heading
        elif h:
            in_more = bool(_MORE.search(h.group(1)))
            sections.append((h.group(1), []))
        elif sections:
            sections[-1][1].append(line)
    if len(sections) < 2:
        return None

    def find(pattern: str):
        return next(((t, b) for t, b in sections if re.search(pattern, t, re.I)), None)

    meaning = find(r"mean for|mean to|means for|what.*mean")
    related = find(r"related|connected|blood tests? (?:linked|that)")
    actions = find(r"what can you|can you do|protect|do next|you can do")
    more = find(r"explore|learn more|more about")
    condition = next(((t, b) for t, b in sections if (t, b) not in (meaning, related, actions, more)), None)
    if condition is None or meaning is None:
        return None
    condition_paras = _paragraphs(condition[1])
    meaning_paras = _paragraphs(meaning[1])
    if not condition_paras or not meaning_paras:
        return None

    tests: list[RelatedTest] = []
    if related and markers:
        from app.pipeline.presentation import _finding_from_marker

        seen: set[str] = set()
        for line in related[1]:
            m = _BULLET.match(line)
            if not m:
                continue
            key, why = _split_item(m.group(1))
            marker = _marker_for(key, markers)
            if marker is None or marker.key in seen or marker.value is None:
                continue  # a test the report does not hold is never shown
            seen.add(marker.key)
            tests.append(RelatedTest(finding=_finding_from_marker(marker), why=why))
            if len(tests) == MAX_RELATED:
                break

    acts: list[ExplainerAction] = []
    if actions:
        for line in actions[1]:
            m = _BULLET.match(line)
            if m:
                title, detail = _split_item(m.group(1))
                if title:
                    acts.append(ExplainerAction(title=title, detail=detail, icon=action_icon(title) if action_icon(title) != "habit" else action_icon(detail)))
            if len(acts) == MAX_ACTIONS:
                break

    extra: list[ExplainerSection] = []
    if more:
        cur: ExplainerSection | None = None
        for line in more[1]:
            h = _H3.match(line)
            if h:
                cur = ExplainerSection(title=h.group(1).strip())
                extra.append(cur)
                continue
            b = _BULLET.match(line)
            if b and cur is not None and len(cur.items) < MAX_ITEMS:
                item = b.group(1).replace("**", "").strip()
                if not _NOTE.search(item):
                    cur.items.append(item)
        extra = [s for s in extra if s.items]

    return RiskExplanation(
        condition_title=condition[0].strip(),
        condition=condition_paras,
        score_card=score_card_for(risk) if risk is not None else None,
        meaning_title=meaning[0].strip(),
        meaning=meaning_paras,
        related_tests=tests,
        actions=acts,
        more=extra,
    )
