"""Hardware calculator: convert guess numbers to crack times."""

from __future__ import annotations

from crack_time.hardware.hash_rates import resolve_hash_rate
from crack_time.hardware.tiers import HARDWARE_TIERS, get_tier


def crack_time_seconds(
    guess_number: int | float, algorithm: str, hardware_tier: str
) -> float:
    """Calculate crack time in seconds."""
    base_rate = resolve_hash_rate(algorithm)
    tier = get_tier(hardware_tier)
    multiplier = tier["multiplier"]
    effective_rate = base_rate * multiplier

    if effective_rate == 0:
        return float("inf")
    return guess_number / effective_rate


def effective_hash_rate(algorithm: str, hardware_tier: str) -> float:
    """Calculate the effective hash rate for a given algorithm and tier."""
    base_rate = resolve_hash_rate(algorithm)
    tier = get_tier(hardware_tier)
    return base_rate * tier["multiplier"]
