"""Tests for the sequence estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.sequence import SequenceEstimator


def test_sequence_ascending_lowercase():
    analysis = analyze("abcdefgh")
    est = SequenceEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    assert len(result.matches) > 0


def test_sequence_descending():
    analysis = analyze("hgfedcba")
    est = SequenceEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # Descending gets 2x multiplier
    ascending_analysis = analyze("abcdefgh")
    ascending_result = est.estimate(ascending_analysis)
    assert result.guess_number >= ascending_result.guess_number


def test_sequence_digits():
    analysis = analyze("12345")
    est = SequenceEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")


def test_sequence_no_sequence():
    analysis = analyze("axbycz")
    est = SequenceEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")


def test_sequence_too_short():
    analysis = analyze("ab")
    est = SequenceEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")
