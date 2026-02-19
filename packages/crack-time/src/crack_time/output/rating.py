"""Strength rating: time-based 0-4 scale."""

from __future__ import annotations

SECONDS_PER_MINUTE = 60
SECONDS_PER_DAY = 86_400
SECONDS_PER_YEAR = 31_557_600  # 365.25 days

RATING_LABELS = {
    0: "CRITICAL",
    1: "WEAK",
    2: "FAIR",
    3: "STRONG",
    4: "VERY STRONG",
}


def compute_rating(crack_time_secs: float) -> int:
    """Compute strength rating from crack time in seconds.

    Rating 0 (CRITICAL): < 1 minute
    Rating 1 (WEAK):     < 1 day
    Rating 2 (FAIR):     < 1 year
    Rating 3 (STRONG):   < 100 years
    Rating 4 (VERY STRONG): >= 100 years
    """
    if crack_time_secs < SECONDS_PER_MINUTE:
        return 0
    if crack_time_secs < SECONDS_PER_DAY:
        return 1
    if crack_time_secs < SECONDS_PER_YEAR:
        return 2
    if crack_time_secs < SECONDS_PER_YEAR * 100:
        return 3
    return 4


def rating_label(rating: int) -> str:
    return RATING_LABELS.get(rating, "UNKNOWN")
