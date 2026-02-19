"""Mask estimator: per-position charset size product with priority ordering."""

from __future__ import annotations

from crack_time.data import load_mask_library
from crack_time.estimators.base import Estimator
from crack_time.types import EstimateResult, PasswordAnalysis

MASK_CLASSES = {
    "?l": 26,
    "?u": 26,
    "?d": 10,
    "?s": 33,
}


def char_to_mask_class(c: str) -> str:
    if c.islower():
        return "?l"
    if c.isupper():
        return "?u"
    if c.isdigit():
        return "?d"
    return "?s"


def mask_guesses(password: str) -> int:
    """Compute keyspace for the mask pattern of this password."""
    guesses = 1
    for c in password:
        guesses *= MASK_CLASSES[char_to_mask_class(c)]
    return guesses


def mask_guesses_with_priority(password: str, mask_library: list[dict]) -> int:
    """Compute mask guess number accounting for attacker priority ordering."""
    password_mask = "".join(char_to_mask_class(c) for c in password)
    password_keyspace = mask_guesses(password)

    cumulative_guesses = 0
    for entry in mask_library:
        if entry["mask"] == password_mask:
            return cumulative_guesses + password_keyspace // 2
        cumulative_guesses += entry["keyspace"]

    return password_keyspace


class MaskEstimator(Estimator):
    name = "mask"
    display_name = "Mask Attack"
    phase = 1
    estimator_type = "whole_password"

    def estimate(self, analysis: PasswordAnalysis) -> EstimateResult:
        if analysis.length == 0:
            return EstimateResult(
                guess_number=float("inf"),
                attack_name=self.display_name,
            )

        mask_library = load_mask_library()
        guesses = mask_guesses_with_priority(analysis.password, mask_library)
        password_mask = "".join(
            char_to_mask_class(c) for c in analysis.password
        )

        return EstimateResult(
            guess_number=guesses,
            attack_name=self.display_name,
            details={
                "mask": password_mask,
                "keyspace": mask_guesses(analysis.password),
            },
        )
