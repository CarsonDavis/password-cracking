"""Tests for Match/PasswordAnalysis construction."""

from crack_time.types import (
    BruteforceMatch,
    DateMatch,
    DecompositionResult,
    DictionaryMatch,
    EstimateResult,
    KeyboardWalkMatch,
    L33tMatch,
    Match,
    PasswordAnalysis,
    RepeatMatch,
    SequenceMatch,
    SimulationResult,
)


def test_match_construction():
    m = Match(pattern="test", token="abc", i=0, j=2)
    assert m.pattern == "test"
    assert m.token == "abc"
    assert m.i == 0
    assert m.j == 2
    assert m.guesses == 0


def test_dictionary_match():
    m = DictionaryMatch(
        pattern="dictionary", token="password", i=0, j=7,
        word="password", rank=1, dictionary_name="common_passwords",
    )
    assert m.rank == 1
    assert m.reversed is False


def test_l33t_match():
    m = L33tMatch(
        pattern="l33t", token="p@ss", i=0, j=3,
        word="pass", rank=50, dictionary_name="common_passwords",
        sub_table={"a": "@"},
    )
    assert m.sub_table == {"a": "@"}


def test_keyboard_walk_match():
    m = KeyboardWalkMatch(
        pattern="spatial", token="qwerty", i=0, j=5,
        graph="qwerty", turns=1, shifted_count=0,
    )
    assert m.graph == "qwerty"
    assert m.turns == 1


def test_sequence_match():
    m = SequenceMatch(
        pattern="sequence", token="abc", i=0, j=2,
        sequence_name="lower", ascending=True, delta=1,
    )
    assert m.ascending is True


def test_date_match():
    m = DateMatch(
        pattern="date", token="01151987", i=0, j=7,
        year=1987, month=1, day=15, separator="", has_separator=False,
    )
    assert m.year == 1987


def test_repeat_match():
    m = RepeatMatch(
        pattern="repeat", token="aaa", i=0, j=2,
        base_token="a", base_guesses=26, repeat_count=3,
    )
    assert m.repeat_count == 3


def test_password_analysis():
    analysis = PasswordAnalysis(
        password="abc123", length=6,
        charsets={"lower", "digit"}, cardinality=36,
    )
    assert analysis.length == 6
    assert analysis.cardinality == 36
    assert analysis.matches == []


def test_password_analysis_matches_of_type():
    analysis = PasswordAnalysis(password="test", length=4)
    m1 = DictionaryMatch(pattern="dictionary", token="test", i=0, j=3, rank=5)
    m2 = SequenceMatch(pattern="sequence", token="test", i=0, j=3)
    analysis.matches = [m1, m2]
    assert len(analysis.matches_of_type("dictionary")) == 1
    assert len(analysis.matches_of_type("sequence")) == 1


def test_estimate_result():
    r = EstimateResult(guess_number=100, attack_name="test")
    assert r.guess_number == 100
    assert r.matches == []


def test_decomposition_result():
    r = DecompositionResult(guesses=100, sequence=[], log10_guesses=2.0)
    assert r.guesses == 100


def test_bruteforce_match():
    m = BruteforceMatch(
        pattern="brute_force", token="abc", i=0, j=2,
        guesses=17576, cardinality=26,
    )
    assert m.cardinality == 26
