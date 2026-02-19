"""Sequence estimator: base_start * length * direction_mult."""

from __future__ import annotations

from crack_time.estimators.base import Estimator
from crack_time.types import EstimateResult, PasswordAnalysis, SequenceMatch


_WELL_KNOWN_SEQUENCES = frozenset({
    "0123456789", "abcdefghij", "qwertyuiop",
    "abcdefgh", "abcdef", "abc", "123", "1234", "12345", "123456",
})


class SequenceEstimator(Estimator):
    name = "sequence"
    display_name = "Sequence Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")

        for match in analysis.matches:
            if not isinstance(match, SequenceMatch):
                continue

            guesses = _sequence_guesses(match)

            scored = SequenceMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                sequence_name=match.sequence_name,
                ascending=match.ascending,
                delta=match.delta,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )


def _sequence_guesses(match: SequenceMatch) -> int:
    first_char = match.token[0]
    if first_char.isdigit():
        base_guesses = 10
    elif first_char.islower():
        base_guesses = 26
    elif first_char.isupper():
        base_guesses = 26
    else:
        base_guesses = 95

    if match.token.lower() in _WELL_KNOWN_SEQUENCES:
        base_guesses = 4

    guesses = base_guesses * len(match.token)

    if not match.ascending:
        guesses *= 2

    return max(guesses, 1)
