"""Turn the nutrition overview answer into cards: priorities, foods to include, foods to limit."""

from __future__ import annotations

import re

from app.contracts.presentation import NutritionFood, NutritionPlan, NutritionPriority

_HEADING = re.compile(r"^#{2,3}\s+(.+?)\s*$")
_BULLET = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+(.*\S)\s*$")
_SECTIONS = (
    ("priorities", re.compile(r"body needs|priorit|what to focus", re.I)),
    ("include", re.compile(r"include|eat more|add more|foods to (?:add|favou?r|choose)", re.I)),
    ("limit", re.compile(r"limit|cut back|reduce|go easy|eat less", re.I)),
)
MAX_PRIORITIES, MAX_INCLUDE, MAX_LIMIT = 3, 6, 3

_ICONS = (
    (r"spinach|methi|fenugreek|kale|greens?|leafy|palak|lettuce|broccoli|cabbage", "\U0001F96C"),
    (r"lentil|dal|chickpea|chana|rajma|beans?|legume|moong|sprouts?", "\U0001FAD8"),
    (r"oats?|millet|ragi|jowar|bajra|brown rice|whole grain|quinoa|roti|wheat|barley", "\U0001F33E"),
    (r"almond|walnut|nuts?|peanut|seeds?|flax|chia|pumpkin seed", "\U0001F330"),
    (r"fish|salmon|sardine|mackerel|omega", "\U0001F41F"),
    (r"egg", "\U0001F95A"),
    (r"curd|yogh?urt|dahi|milk|paneer|cheese|buttermilk|chaas|dairy", "\U0001F95B"),
    (r"orange|citrus|lemon|amla|guava|papaya|kiwi|berr|apple|banana|fruit|pomegranate|mango", "\U0001F34A"),
    (r"carrot|tomato|beet|pepper|capsicum|vegetable|pumpkin|gourd|okra|bhindi|cucumber", "\U0001F955"),
    (r"turmeric|haldi|ginger|garlic|spice|cumin|jeera", "\U0001F9C4"),
    (r"olive|mustard oil|oil|ghee|avocado", "\U0001FAD2"),
    (r"chicken|meat|mutton|tofu|soy|protein", "\U0001F357"),
    (r"water|coconut|tea|juice|drink|beverage|soda|cola", "\U0001F964"),
    (r"fried|samosa|pakora|chips|namkeen|fast food|junk|processed|packaged|bhujia", "\U0001F35F"),
    (r"sugar|sweet|dessert|mithai|cake|biscuit|cookie|candy|chocolate|jaggery", "\U0001F36C"),
    (r"salt|pickle|achar|papad|sodium", "\U0001F9C2"),
    (r"white rice|maida|refined|bread|white flour", "\U0001F35E"),
)


def food_icon(name: str) -> str:
    for pattern, icon in _ICONS:
        if re.search(pattern, name or "", re.I):
            return icon
    return "\U0001F37D️"


def _split_item(text: str) -> tuple[str, str]:
    m = re.match(r"\*\*(.+?)\*\*\s*[:.,]?\s*(.*)$", text)
    if m:
        name, rest = m.group(1).strip(" :"), m.group(2).strip()
    elif ":" in text[:60]:
        name, rest = (p.strip() for p in text.split(":", 1))
    else:
        name, rest = text.strip(), ""
    return name.replace("**", "").strip(), rest.replace("**", "").strip()


def parse_nutrition_plan(text: str) -> tuple[str, NutritionPlan] | None:
    """Return (opening text, plan), or None when the answer does not follow the layout."""
    opening: list[str] = []
    buckets: dict[str, list[str]] = {"priorities": [], "include": [], "limit": []}
    current: str | None = None
    for line in (text or "").split("\n"):
        heading = _HEADING.match(line)
        if heading:
            current = next((key for key, pattern in _SECTIONS if pattern.search(heading.group(1))), "other")
            continue
        if current is None:
            opening.append(line)
        elif current in buckets:
            bullet = _BULLET.match(line)
            if bullet:
                buckets[current].append(bullet.group(1))
    priorities = []
    for item in buckets["priorities"][:MAX_PRIORITIES]:
        title, why = _split_item(item)
        if title:
            priorities.append(NutritionPriority(title=title, why=why))
    include = []
    for item in buckets["include"][:MAX_INCLUDE]:
        name, why = _split_item(item)
        if name:
            include.append(NutritionFood(name=name, why=why, icon=food_icon(name)))
    limit = []
    for item in buckets["limit"][:MAX_LIMIT]:
        name, why = _split_item(item)
        if name:
            limit.append(NutritionFood(name=name, why=why, icon=food_icon(name)))
    if len(include) < 3:
        return None
    intro = re.sub(r"\n{3,}", "\n\n", "\n".join(opening)).strip()
    return intro, NutritionPlan(priorities=priorities, include=include, limit=limit)
