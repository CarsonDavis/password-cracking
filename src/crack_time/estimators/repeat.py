"""Repeat estimator: base_guesses * repeat_count."""

from __future__ import annotations

from crack_time.analysis.character_classes import bruteforce_guesses
from crack_time.estimators.base import Estimator
from crack_time.types import EstimateResult, PasswordAnalysis, RepeatMatch


class RepeatEstimator(Estimator):
    name = "repeat"
    display_name = "Repeat Pattern Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")

        for match in analysis.matches:
            if not isinstance(match, RepeatMatch):
                continue

            # Compute base_guesses for the base token
            base_guesses = bruteforce_guesses(match.base_token)
            guesses = base_guesses * match.repeat_count

            scored = RepeatMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                base_token=match.base_token,
                base_guesses=base_guesses,
                repeat_count=match.repeat_count,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )


