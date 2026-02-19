"""Repeat pattern detection with recursive base analysis."""

from __future__ import annotations

import re

from crack_time.types import RepeatMatch


def detect_repeats(password: str) -> list[RepeatMatch]:
    """Detect repeated characters or substrings using greedy and lazy regex."""
    matches: list[RepeatMatch] = []
    n = len(password)
    if n < 2:
        return matches

    # Greedy: find longest repeated sequence
    for m in re.finditer(r"(.+)\1+", password):
        base = m.group(1)
        full = m.group(0)
        repeat_count = len(full) // len(base)
        matches.append(
            RepeatMatch(
                pattern="repeat",
                token=full,
                i=m.start(),
                j=m.end() - 1,
                base_token=base,
                base_guesses=0,  # Set later by estimator
                repeat_count=repeat_count,
            )
        )

    # Lazy: find shortest repeating unit
    for m in re.finditer(r"(.+?)\1+", password):
        base = m.group(1)
        full = m.group(0)
        repeat_count = len(full) // len(base)
        # Only add if different from greedy matches at same position
        already_exists = any(
            existing.i == m.start() and existing.j == m.end() - 1
            and existing.base_token == base
            for existing in matches
        )
        if not already_exists:
            matches.append(
                RepeatMatch(
                    pattern="repeat",
                    token=full,
                    i=m.start(),
                    j=m.end() - 1,
                    base_token=base,
                    base_guesses=0,
                    repeat_count=repeat_count,
                )
            )

    return matches
