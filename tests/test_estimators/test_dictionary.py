"""Tests for the dictionary estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.dictionary import DictionaryEstimator


def test_dictionary_password_rank_1():
    analysis = analyze("password")
    est = DictionaryEstimator()
    result = est.estimate(analysis)
    # "password" is rank 1, all lowercase -> guesses = 1 * 1 = 1
    assert result.guess_number == 1
    assert len(result.matches) > 0


def test_dictionary_dragon():
    analysis = analyze("dragon")
    est = DictionaryEstimator()
    result = est.estimate(analysis)
    assert result.guess_number > 0
    assert result.guess_number != float("inf")


def test_dictionary_capitalized():
    """First-letter capitalization doubles guesses."""
    analysis = analyze("Password")
    est = DictionaryEstimator()
    result = est.estimate(analysis)
    # rank 1 * uppercase_variations("Password") = 1 * 2 = 2
    assert result.guess_number == 2


def test_dictionary_no_match():
    analysis = analyze("zqjxvkwm")
    est = DictionaryEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")


def test_dictionary_reversed():
    """Reversed words should be detected with 2x multiplier."""
    analysis = analyze("drowssap")  # "password" reversed
    est = DictionaryEstimator()
    result = est.estimate(analysis)
    # Should find "password" reversed: rank=1 * 1 (lowercase) * 2 (reversed) = 2
    assert result.guess_number <= 2
