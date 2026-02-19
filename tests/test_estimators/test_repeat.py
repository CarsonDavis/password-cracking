"""Tests for the repeat estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.repeat import RepeatEstimator


def test_repeat_single_char():
    analysis = analyze("aaaaaa")
    est = RepeatEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # base "a" has cardinality 26 (lowercase), length 1 -> base_guesses = 26
    # repeat_count = 6 -> guesses = 26 * 6 = 156
    assert result.guess_number == 26 * 6


def test_repeat_substring():
    analysis = analyze("abcabc")
    est = RepeatEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    assert len(result.matches) > 0


def test_repeat_no_repeat():
    analysis = analyze("abcdef")
    est = RepeatEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")


def test_repeat_two_chars():
    analysis = analyze("ababab")
    est = RepeatEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # base "ab" -> cardinality=26, length=2 -> base_guesses=676
    # repeat_count=3 -> 676*3=2028
    assert result.guess_number == 26 ** 2 * 3
