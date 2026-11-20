"""Topic risk for the "no evidence" policy (production readiness plan, 4.6).

Low risk education (diet, sleep, exercise, what a marker is) may be answered from model
knowledge with a "general information" label. High risk topics need reviewed evidence or
a polite redirect to a clinician.
"""

from __future__ import annotations

import re

from app.pipeline.red_flags import normalize_text

HIGH_RISK_TOPICS: dict[str, re.Pattern[str]] = {
    "medication": re.compile(
        r"\b(drug|drugs|medicine|medication|tablet|pill|dose|dosage|mg|side effects?|interaction\w*|"
        r"antibiotic\w*|steroid\w*|insulin(?! resistance)|statin\w*|supplement dose|dawai|goli)\b",
        re.I,
    ),
    "pregnancy": re.compile(r"\b(pregnan\w*|trimester|breastfeed\w*|lactat\w*|ivf|miscarriage|garbh\w*)\b", re.I),
    "children": re.compile(r"\b(baby|babies|infant|newborn|toddler|child|children|kid|kids|paediatric|pediatric|bachch?a)\b", re.I),
    "cancer": re.compile(r"\b(cancer|tumou?r|malignan\w*|chemo\w*|oncolog\w*|metasta\w*|carcinoma|lymphoma|leukemia)\b", re.I),
    "stopping_treatment": re.compile(
        r"\b(stop|quit|skip|discontinue|come off|give up)\b.{0,30}\b(treatment|therapy|dialysis|medicine|medication)\b",
        re.I,
    ),
}


_INSULIN_THERAPY = re.compile(
    r"\b(?:take|taking|inject\w*|start|starting|stop|stopping|skip\w*|miss\w*|dose|doses|dosage|units?|pen|pump|"
    r"lantus|mixtard|basal|bolus|shot|shots|syringe|needle)\b",
    re.I,
)


def _insulin_is_a_test(text: str) -> bool:
    """"Compare my sugar and insulin" asks about a blood result, not about the medicine."""
    if "insulin" not in text or _INSULIN_THERAPY.search(text):
        return False
    rest = re.sub(r"\binsulin\b", " ", text)
    return not HIGH_RISK_TOPICS["medication"].search(rest)


def high_risk_topics(message: str) -> list[str]:
    text = normalize_text(message)
    topics = [name for name, pattern in HIGH_RISK_TOPICS.items() if pattern.search(text)]
    if "medication" in topics and _insulin_is_a_test(text):
        topics.remove("medication")
    return topics


def is_high_risk_topic(message: str) -> bool:
    return bool(high_risk_topics(message))
