"""Character class detection and cardinality computation."""

from __future__ import annotations

CHARSET_SIZES = {
    "lower": 26,
    "upper": 26,
    "digit": 10,
    "special": 33,
}


def detect_charsets(password: str) -> set[str]:
    """Identify which character classes are present in the password."""
    charsets: set[str] = set()
    for c in password:
        if c.islower():
            charsets.add("lower")
        elif c.isupper():
            charsets.add("upper")
        elif c.isdigit():
            charsets.add("digit")
        else:
            charsets.add("special")
    return charsets


def compute_cardinality(charsets: set[str]) -> int:
    """Sum of charset sizes for all groups present."""
    return sum(CHARSET_SIZES.get(cs, 0) for cs in charsets)


def bruteforce_guesses(token: str) -> int:
    """Compute brute-force guess count for a token: cardinality^length."""
    if not token:
        return 1
    charsets = detect_charsets(token)
    cardinality = compute_cardinality(charsets)
    return max(cardinality ** len(token), 1)
