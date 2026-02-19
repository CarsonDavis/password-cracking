"""Password crack-time simulator with analytical estimators."""

from crack_time.simulator import estimate_password


def estimate(password: str, algorithm: str = "bcrypt_cost12",
             hardware_tier: str = "consumer") -> dict:
    """Convenience function for estimating password crack time.

    Returns a dict with crack_time_seconds, rating, winning_attack, etc.
    """
    result = estimate_password(password, algorithm, hardware_tier)
    return result
