"""L33t estimator: rank * uppercase_vars * l33t_vars."""

from __future__ import annotations

from crack_time.data import load_l33t_table
from crack_time.estimators.base import Estimator
from crack_time.estimators.scoring import l33t_variations, uppercase_variations
from crack_time.types import EstimateResult, L33tMatch, PasswordAnalysis


class L33tEstimator(Estimator):
    name = "l33t"
    display_name = "L33t Dictionary Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")
        l33t_table = load_l33t_table()

        for match in analysis.matches:
            if not isinstance(match, L33tMatch):
                continue

            guesses = match.rank
            guesses *= uppercase_variations(match.token)
            guesses *= l33t_variations(match.word, l33t_table)
            guesses = max(guesses, 1)

            scored = L33tMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                word=match.word,
                rank=match.rank,
                dictionary_name=match.dictionary_name,
                sub_table=match.sub_table,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )
