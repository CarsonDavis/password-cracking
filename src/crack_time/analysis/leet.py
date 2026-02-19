"""L33t-speak detection and de-substitution."""

from __future__ import annotations

import itertools

from crack_time.data import Wordlist
from crack_time.types import L33tMatch


def _build_inverse_table(l33t_table: dict[str, list[str]]) -> dict[str, list[str]]:
    """Build inverse mapping: l33t_char -> list of possible original chars."""
    inverse: dict[str, list[str]] = {}
    for original, subs in l33t_table.items():
        for sub in subs:
            inverse.setdefault(sub, []).append(original)
    return inverse


def detect_l33t_matches(
    password: str,
    l33t_table: dict[str, list[str]],
    wordlists: dict[str, Wordlist],
) -> list[L33tMatch]:
    """Detect l33t-substituted dictionary words in the password."""
    inverse_table = _build_inverse_table(l33t_table)
    matches: list[L33tMatch] = []
    n = len(password)

    for i in range(n):
        for j in range(i + 1, n):
            token = password[i : j + 1]

            # Find positions that have l33t substitutions
            l33t_positions: list[tuple[int, str, list[str]]] = []
            for pos, char in enumerate(token):
                if char in inverse_table:
                    l33t_positions.append((pos, char, inverse_table[char]))

            if not l33t_positions:
                continue  # No l33t chars in this substring

            # Cap enumeration at 2^10
            total_combos = 1
            for _, _, originals in l33t_positions:
                total_combos *= len(originals) + 1  # +1 for keeping original
                if total_combos > 1024:
                    break

            if total_combos > 1024:
                # Cap at 1024 combinations to avoid exponential blowup.
                # The options list places de-l33t replacements before the original char,
                # so itertools.product explores actual substitutions first — this means
                # the 1024 cap preferentially checks combinations with more substitutions.
                options = [originals + [char] for _, char, originals in l33t_positions]
                combos = list(itertools.islice(itertools.product(*options), 1024))
            else:
                options = [originals + [char] for _, char, originals in l33t_positions]
                combos = list(itertools.product(*options))

            for combo in combos:
                chars = list(token.lower())
                sub_table: dict[str, str] = {}
                any_sub = False

                for idx, (pos, orig_char, _originals) in enumerate(l33t_positions):
                    replacement = combo[idx]
                    if replacement != orig_char:
                        chars[pos] = replacement
                        sub_table[replacement] = orig_char
                        any_sub = True

                if not any_sub:
                    continue  # No actual substitution made

                de_l33ted = "".join(chars)
                for dict_name, wordlist in wordlists.items():
                    rank = wordlist.rank(de_l33ted)
                    if rank > 0:
                        matches.append(
                            L33tMatch(
                                pattern="l33t",
                                token=token,
                                i=i,
                                j=j,
                                word=de_l33ted,
                                rank=rank,
                                dictionary_name=dict_name,
                                sub_table=sub_table,
                            )
                        )

    return matches
