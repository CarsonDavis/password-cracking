"""O(n^2) substring matching against frequency-ranked wordlists."""

from __future__ import annotations

from crack_time.data import Wordlist
from crack_time.types import DictionaryMatch


def detect_dictionary_matches(
    password: str, wordlists: dict[str, Wordlist]
) -> list[DictionaryMatch]:
    """Check every substring of password against all wordlists.

    Also checks reversed substrings for reversed dictionary matches.
    """
    matches: list[DictionaryMatch] = []
    n = len(password)

    for i in range(n):
        for j in range(i, n):
            token = password[i : j + 1]
            if len(token) < 2:
                continue
            token_lower = token.lower()
            token_reversed = token_lower[::-1]

            for dict_name, wordlist in wordlists.items():
                # Forward match
                rank = wordlist.rank(token_lower)
                if rank > 0:
                    matches.append(
                        DictionaryMatch(
                            pattern="dictionary",
                            token=token,
                            i=i,
                            j=j,
                            word=token_lower,
                            rank=rank,
                            dictionary_name=dict_name,
                            reversed=False,
                        )
                    )
                # Reversed match
                if token_reversed != token_lower:
                    rank = wordlist.rank(token_reversed)
                    if rank > 0:
                        matches.append(
                            DictionaryMatch(
                                pattern="dictionary",
                                token=token,
                                i=i,
                                j=j,
                                word=token_reversed,
                                rank=rank,
                                dictionary_name=dict_name,
                                reversed=True,
                            )
                        )

    return matches
