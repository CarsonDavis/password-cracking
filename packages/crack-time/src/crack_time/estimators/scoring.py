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


def l33t_variations(word: str, l33t_table: dict[str, list[str]]) -> int:
    """Compute l33t variation multiplier: total l33t renderings of the word.

    For each character, the attacker must try: keep original + each l33t
    substitution. The product across all positions gives the full search space.
    """
    if not word:
        return 1
    variations = 1
    for char in word:
        n_subs = len(l33t_table.get(char, []))
        variations *= 1 + n_subs  # keep original + each l33t option
    return max(variations, 1)
