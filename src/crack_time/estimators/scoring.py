"""Shared scoring helper functions for estimators."""

from __future__ import annotations

from math import comb


def uppercase_variations(token: str) -> int:
    """Compute uppercase variation multiplier (from zxcvbn)."""
    if token == token.lower():
        return 1  # all lowercase
    if token == token.upper():
        return 2  # all uppercase
    if len(token) > 1 and token[0].isupper() and token[1:] == token[1:].lower():
        return 2  # first-letter-cap
    # Mixed case: sum of C(n, k) for k=1..min(U, n-U)
    n = len(token)
    u = sum(1 for c in token if c.isupper())
    return sum(comb(n, k) for k in range(1, min(u, n - u) + 1))


def l33t_variations(token: str, sub_table: dict[str, str]) -> int:
    """Compute l33t substitution variation multiplier (from zxcvbn).

    sub_table maps original_char -> l33t_char.
    """
    if not sub_table:
        return 1
    variations = 1
    for original_char, l33t_char in sub_table.items():
        s = sum(1 for c in token if c == l33t_char)
        u = sum(1 for c in token if c == original_char)
        if s == 0:
            continue
        variations *= sum(comb(s + u, k) for k in range(1, s + 1))
    return max(variations, 2)  # minimum 2 for any l33t substitution
