"""Tests for the DP decomposition engine."""

from crack_time.decomposition.dp_engine import (
    bruteforce_guesses,
    minimum_guess_decomposition,
)
from crack_time.types import DictionaryMatch, Match, SequenceMatch


def test_dp_empty_password():
    result = minimum_guess_decomposition("", [])
    assert result.guesses == 0
    assert result.sequence == []


def test_dp_no_matches_falls_back_to_brute_force():
    result = minimum_guess_decomposition("abc", [])
    assert result.guesses == 26 ** 3  # brute-force for lowercase
    assert len(result.sequence) == 1
    assert result.sequence[0].pattern == "brute_force"


def test_dp_single_match_covering_full_password():
    match = DictionaryMatch(
        pattern="dictionary", token="password", i=0, j=7,
        guesses=1, word="password", rank=1,
    )
    result = minimum_guess_decomposition("password", [match])
    assert result.guesses == 1
    assert len(result.sequence) == 1


def test_dp_two_matches_concatenated():
    m1 = DictionaryMatch(
        pattern="dictionary", token="pass", i=0, j=3,
        guesses=50, word="pass", rank=50,
    )
    m2 = SequenceMatch(
        pattern="sequence", token="123", i=4, j=6,
        guesses=30, sequence_name="digit", ascending=True, delta=1,
    )
    result = minimum_guess_decomposition("pass123", [m1, m2])
    assert result.guesses == 50 * 30  # 1500
    assert len(result.sequence) == 2


def test_dp_picks_cheaper_match():
    """When two matches cover the same substring, DP picks the cheaper one."""
    expensive = Match(pattern="spatial", token="qwerty", i=0, j=5, guesses=1000)
    cheap = DictionaryMatch(
        pattern="dictionary", token="qwerty", i=0, j=5,
        guesses=4, word="qwerty", rank=4,
    )
    result = minimum_guess_decomposition("qwerty", [expensive, cheap])
    assert result.guesses == 4


def test_dp_with_gap():
    """If matches don't cover the full password, gaps are brute-forced."""
    match = DictionaryMatch(
        pattern="dictionary", token="pass", i=0, j=3,
        guesses=50, word="pass", rank=50,
    )
    result = minimum_guess_decomposition("pass!!!", [match])
    # "pass" = 50 guesses, "!!!" = 33^3 = 35937 brute-force
    # Total = 50 * 35937
    assert result.guesses <= 50 * (33 ** 3)


def test_dp_overlapping_matches():
    """Overlapping matches should be handled correctly."""
    m1 = Match(pattern="dict", token="abcd", i=0, j=3, guesses=10)
    m2 = Match(pattern="dict", token="cdef", i=2, j=5, guesses=10)
    m3 = Match(pattern="dict", token="abcdef", i=0, j=5, guesses=100)
    result = minimum_guess_decomposition("abcdef", [m1, m2, m3])
    # The DP should find the best non-overlapping combination
    assert result.guesses <= 100


def test_bruteforce_guesses_lowercase():
    assert bruteforce_guesses("abc") == 26 ** 3


def test_bruteforce_guesses_mixed():
    assert bruteforce_guesses("aB1") == 62 ** 3  # lower+upper+digit = 62


def test_bruteforce_guesses_empty():
    assert bruteforce_guesses("") == 1
