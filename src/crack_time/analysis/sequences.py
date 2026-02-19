"""Constant-delta character sequence detection."""

from __future__ import annotations

from crack_time.types import SequenceMatch

MIN_SEQUENCE_LENGTH = 3
ALLOWED_DELTAS = {1, -1, 2, -2}


def detect_sequences(password: str) -> list[SequenceMatch]:
    """Detect constant-delta character sequences in the password."""
    matches: list[SequenceMatch] = []
    n = len(password)
    if n < MIN_SEQUENCE_LENGTH:
        return matches

    i = 0
    while i < n - 1:
        delta = ord(password[i + 1]) - ord(password[i])
        if abs(delta) not in {1, 2}:
            i += 1
            continue

        j = i + 2
        while j < n and ord(password[j]) - ord(password[j - 1]) == delta:
            j += 1

        length = j - i
        if length >= MIN_SEQUENCE_LENGTH:
            token = password[i:j]
            seq_name = _classify_sequence(token)
            matches.append(
                SequenceMatch(
                    pattern="sequence",
                    token=token,
                    i=i,
                    j=j - 1,
                    sequence_name=seq_name,
                    ascending=delta > 0,
                    delta=delta,
                )
            )
            i = j
        else:
            i += 1

    return matches


def _classify_sequence(token: str) -> str:
    """Classify the sequence type based on the characters."""
    if token[0].isdigit():
        return "digit"
    elif token[0].islower():
        return "lower"
    elif token[0].isupper():
        return "upper"
    return "unicode"
