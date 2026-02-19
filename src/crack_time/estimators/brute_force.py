"""Brute force estimator: charset^length."""

from __future__ import annotations

from crack_time.estimators.base import Estimator
from crack_time.types import EstimateResult, PasswordAnalysis


class BruteForceEstimator(Estimator):
    name = "brute_force"
    display_name = "Brute Force"
    phase = 1
    estimator_type = "whole_password"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        if analysis.length == 0:
            return EstimateResult(
                guess_number=0,
                attack_name=self.display_name,
                details={"cardinality": 0, "length": 0},
            )

        guesses = analysis.cardinality ** analysis.length
        return EstimateResult(
            guess_number=guesses,
            attack_name=self.display_name,
            details={
                "cardinality": analysis.cardinality,
                "length": analysis.length,
            },
        )
