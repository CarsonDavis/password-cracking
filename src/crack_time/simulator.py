"""Top-level orchestrator: runs the full simulation pipeline."""

from __future__ import annotations

from crack_time.analysis.analyzer import analyze
from crack_time.decomposition.dp_engine import minimum_guess_decomposition
from crack_time.estimators.base import Estimator, discover_estimators
from crack_time.hardware.calculator import crack_time_seconds, effective_hash_rate
from crack_time.output.formatter import format_time
from crack_time.output.rating import compute_rating, rating_label
from crack_time.types import EstimateResult, Match, SimulationResult


def estimate_password(
    password: str,
    algorithm: str = "bcrypt_cost12",
    hardware_tier: str = "consumer",
) -> SimulationResult:
    """Run the full estimation pipeline on a password.

    Flow:
    1. Short-circuit on empty password
    2. Run analyzer
    3. Discover and run all enabled estimators
    4. Pool segment-level matches
    5. Run DP on pooled matches
    6. Collect whole-password guess numbers
    7. final_guesses = min(dp_guesses, *whole_password_guesses)
    8. Convert to crack time
    9. Compute strength rating
    10. Return full result
    """
    eff_rate = effective_hash_rate(algorithm, hardware_tier)

    # 1. Short-circuit on empty password
    if not password or password.replace("\x00", "") == "":
        return SimulationResult(
            password=password,
            hash_algorithm=algorithm,
            hardware_tier=hardware_tier,
            effective_hash_rate=eff_rate,
            guess_number=0,
            crack_time_seconds=0,
            crack_time_display="instant",
            rating=0,
            rating_label="CRITICAL",
            winning_attack="empty_password",
            strategies={},
            decomposition=[],
        )

    # 2. Run analyzer (analyzer handles null byte stripping)
    analysis = analyze(password)

    # 3. Discover and run all enabled estimators
    estimators = discover_estimators()
    results: dict[str, EstimateResult] = {}
    for est in estimators:
        try:
            result = est.estimate(analysis)
            results[est.name] = result
        except Exception:
            results[est.name] = EstimateResult(
                guess_number=float("inf"),
                attack_name=est.display_name,
                details={"error": True},
            )

    # 4. Pool segment-level matches from all estimators
    segment_matches: list[Match] = []
    whole_password_guesses: list[tuple[str, int | float]] = []

    for est in estimators:
        if est.name not in results:
            continue
        r = results[est.name]
        if est.estimator_type == "segment_level":
            segment_matches.extend(r.matches)
        else:
            if r.guess_number != float("inf"):
                whole_password_guesses.append((est.name, r.guess_number))

    # 5. Run DP on pooled matches
    dp_result = minimum_guess_decomposition(password, segment_matches)
    dp_guesses = dp_result.guesses

    # 6-7. final_guesses = min(dp_guesses, *whole_password_guesses)
    final_guesses: int | float = dp_guesses
    winning_attack = "dp_decomposition"

    for name, guess_num in whole_password_guesses:
        if guess_num < final_guesses:
            final_guesses = guess_num
            winning_attack = name

    # Check if DP winner and describe it better
    if winning_attack == "dp_decomposition" and dp_result.sequence:
        patterns = set(m.pattern for m in dp_result.sequence)
        if len(patterns) == 1:
            winning_attack = dp_result.sequence[0].pattern
        else:
            winning_attack = " + ".join(
                m.pattern for m in dp_result.sequence if m.pattern != "brute_force"
            ) or "brute_force"

    # 8. Convert to crack time
    ct_seconds = crack_time_seconds(final_guesses, algorithm, hardware_tier)

    # 9. Compute strength rating
    rating = compute_rating(ct_seconds)
    label = rating_label(rating)

    # Build strategy breakdown
    strategies = {}
    for name, r in results.items():
        strategies[name] = {
            "guess_number": r.guess_number,
            "attack_name": r.attack_name,
            "details": r.details,
        }

    # Build decomposition
    decomposition = []
    for m in dp_result.sequence:
        decomposition.append({
            "segment": m.token,
            "type": m.pattern,
            "guesses": m.guesses,
            "i": m.i,
            "j": m.j,
        })

    return SimulationResult(
        password=password,
        hash_algorithm=algorithm,
        hardware_tier=hardware_tier,
        effective_hash_rate=eff_rate,
        guess_number=final_guesses,
        crack_time_seconds=ct_seconds,
        crack_time_display=format_time(ct_seconds),
        rating=rating,
        rating_label=label,
        winning_attack=winning_attack,
        strategies=strategies,
        decomposition=decomposition,
    )
