"""Dictionary estimator: rank * uppercase_vars * (2 if reversed)."""

from __future__ import annotations

from crack_time.estimators.base import Estimator
from crack_time.estimators.scoring import uppercase_variations
from crack_time.types import DictionaryMatch, EstimateResult, PasswordAnalysis


class DictionaryEstimator(Estimator):
    name = "dictionary"
    display_name = "Dictionary Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")

        for match in analysis.matches:
            if not isinstance(match, DictionaryMatch):
                continue

            guesses = match.rank
            guesses *= uppercase_variations(match.token)
            if match.reversed:
                guesses *= 2
            guesses = max(guesses, 1)

            scored = DictionaryMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                word=match.word,
                rank=match.rank,
                dictionary_name=match.dictionary_name,
                reversed=match.reversed,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )
