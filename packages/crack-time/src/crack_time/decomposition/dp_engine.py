"""DP decomposition engine: find optimal non-overlapping match decomposition."""

from __future__ import annotations

import math
from collections import defaultdict

from crack_time.analysis.character_classes import (
    bruteforce_guesses,
    compute_cardinality,
    detect_charsets,
)
from crack_time.types import BruteforceMatch, DecompositionResult, Match


def minimum_guess_decomposition(
    password: str, all_matches: list[Match]
) -> DecompositionResult:
    """Find the optimal non-overlapping decomposition minimizing total guesses.

    Uses dynamic programming adapted from zxcvbn.
    """
    n = len(password)
    if n == 0:
        return DecompositionResult(guesses=0, sequence=[], log10_guesses=0)

    # Group matches by ending position
    matches_by_end: dict[int, list[Match]] = defaultdict(list)
    for m in all_matches:
        matches_by_end[m.j].append(m)

    # DP arrays
    min_guesses = [0] * n
    best_sequence: list[list[Match]] = [[] for _ in range(n)]

    for k in range(n):
        # Default: brute-force the entire prefix [0..k]
        bf_token = password[: k + 1]
        bf = bruteforce_guesses(bf_token)
        min_guesses[k] = bf
        best_sequence[k] = [
            BruteforceMatch(
                pattern="brute_force",
                token=bf_token,
                i=0,
                j=k,
                guesses=bf,
                cardinality=compute_cardinality(detect_charsets(bf_token)),
            )
        ]

        # Also try extending the optimal solution at k-1 with a single bf char
        if k > 0:
            char_bf = bruteforce_guesses(password[k])
            extend_total = min_guesses[k - 1] * char_bf
            if extend_total < min_guesses[k]:
                char_match = BruteforceMatch(
                    pattern="brute_force",
                    token=password[k],
                    i=k,
                    j=k,
                    guesses=char_bf,
                    cardinality=compute_cardinality(detect_charsets(password[k])),
                )
                min_guesses[k] = extend_total
                best_sequence[k] = best_sequence[k - 1] + [char_match]

        # Try each match ending at position k
        for m in matches_by_end[k]:
            if m.guesses <= 0:
                continue

            if m.i == 0:
                total = m.guesses
            else:
                total = min_guesses[m.i - 1] * m.guesses

            if total < min_guesses[k]:
                min_guesses[k] = total
                if m.i == 0:
                    best_sequence[k] = [m]
                else:
                    best_sequence[k] = best_sequence[m.i - 1] + [m]

    # Fill gaps between matches with brute-force segments
    final_sequence = _fill_gaps(password, best_sequence[n - 1])

    return DecompositionResult(
        guesses=min_guesses[n - 1],
        sequence=final_sequence,
        log10_guesses=math.log10(max(min_guesses[n - 1], 1)),
    )


def _fill_gaps(password: str, sequence: list[Match]) -> list[Match]:
    """Insert brute-force matches for any uncovered positions."""
    if not sequence:
        return sequence

    filled: list[Match] = []
    last_end = -1

    for m in sorted(sequence, key=lambda x: x.i):
        if m.i > last_end + 1:
            gap_token = password[last_end + 1 : m.i]
            gap_guesses = bruteforce_guesses(gap_token)
            filled.append(
                BruteforceMatch(
                    pattern="brute_force",
                    token=gap_token,
                    i=last_end + 1,
                    j=m.i - 1,
                    guesses=gap_guesses,
                    cardinality=compute_cardinality(detect_charsets(gap_token)),
                )
            )
        filled.append(m)
        last_end = m.j

    # Fill trailing gap
    if last_end < len(password) - 1:
        gap_token = password[last_end + 1 :]
        gap_guesses = bruteforce_guesses(gap_token)
        filled.append(
            BruteforceMatch(
                pattern="brute_force",
                token=gap_token,
                i=last_end + 1,
                j=len(password) - 1,
                guesses=gap_guesses,
                cardinality=compute_cardinality(detect_charsets(gap_token)),
            )
        )

    return filled
