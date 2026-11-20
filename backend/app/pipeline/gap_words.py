"""One wording for how far a result sits outside its range, so the same gap is never described four ways.

The size is the distance past the nearest limit as a share of that limit. It describes the report's own
range only and never judges how serious a result is.
"""

from __future__ import annotations


def how_far(value, low, high) -> str | None:
    """"slightly", "moderately" or "clearly" outside the range, or None when inside it or unknown."""
    if value is None:
        return None
    try:
        if high is not None and value > high and high:
            share = (value - high) / abs(high)
        elif low is not None and value < low and low:
            share = (low - value) / abs(low)
        else:
            return None
    except (TypeError, ZeroDivisionError):
        return None
    if share <= 0.10:
        return "slightly"
    if share <= 0.50:
        return "moderately"
    return "clearly"
