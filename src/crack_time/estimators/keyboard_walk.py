"""Keyboard walk estimator: spatial formula from zxcvbn."""

from __future__ import annotations

from math import comb

from crack_time.data import graph_stats, load_adjacency_graph
from crack_time.estimators.base import Estimator
from crack_time.types import EstimateResult, KeyboardWalkMatch, PasswordAnalysis

GRAPH_STATS_CACHE: dict[str, tuple[int, float]] = {}


def _get_graph_stats(graph_name: str) -> tuple[int, float]:
    if graph_name not in GRAPH_STATS_CACHE:
        graph = load_adjacency_graph(graph_name)
        GRAPH_STATS_CACHE[graph_name] = graph_stats(graph)
    return GRAPH_STATS_CACHE[graph_name]


def spatial_guesses(
    length: int, turns: int, shifted: int,
    starting_positions: int, avg_degree: float
) -> int:
    """Compute spatial pattern guess count using zxcvbn formula."""
    guesses = 0
    for walk_len in range(2, length + 1):
        possible_turns = min(turns, walk_len - 1)
        for t in range(1, possible_turns + 1):
            guesses += comb(walk_len - 1, t - 1) * starting_positions * (avg_degree ** t)

    if shifted > 0:
        s = shifted
        u = length - shifted
        if s == 0 or u == 0:
            guesses *= 2
        else:
            guesses *= sum(comb(s + u, k) for k in range(1, min(s, u) + 1))

    return max(int(guesses), 1)


class KeyboardWalkEstimator(Estimator):
    name = "keyboard_walk"
    display_name = "Keyboard Walk Attack"
    phase = 1
    estimator_type = "segment_level"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        scored_matches = []
        best_guess = float("inf")

        for match in analysis.matches:
            if not isinstance(match, KeyboardWalkMatch):
                continue

            starting_positions, avg_degree = _get_graph_stats(match.graph)
            guesses = spatial_guesses(
                length=len(match.token),
                turns=match.turns,
                shifted=match.shifted_count,
                starting_positions=starting_positions,
                avg_degree=avg_degree,
            )

            scored = KeyboardWalkMatch(
                pattern=match.pattern,
                token=match.token,
                i=match.i,
                j=match.j,
                guesses=guesses,
                graph=match.graph,
                turns=match.turns,
                shifted_count=match.shifted_count,
            )
            scored_matches.append(scored)
            best_guess = min(best_guess, guesses)

        return EstimateResult(
            guess_number=best_guess if scored_matches else float("inf"),
            attack_name=self.display_name,
            details={"match_count": len(scored_matches)},
            matches=scored_matches,
        )
