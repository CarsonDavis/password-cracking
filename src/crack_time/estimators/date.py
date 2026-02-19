"""Date estimator: year_range * 365 * separator_multiplier."""

from __future__ import annotations

from crack_time.estimators.base import Estimator
from crack_time.types import DateMatch, EstimateResult, PasswordAnalysis

YEAR_RANGE = 200  # 1900-2099, the full range accepted by _valid_date()
NUM_DAYS_PER_YEAR = 365
SEPARATOR_MULTIPLIER = 4


class DateEstimator(Estimator):
    name = "date"
    display_name = "Date Pattern Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")

        for match in analysis.matches:
            if not isinstance(match, DateMatch):
                continue

            guesses = YEAR_RANGE * NUM_DAYS_PER_YEAR
            if match.has_separator:
                guesses *= SEPARATOR_MULTIPLIER

            scored = DateMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                year=match.year,
                month=match.month,
                day=match.day,
                separator=match.separator,
                has_separator=match.has_separator,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )
