"""Tests for the date estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.date import DateEstimator


def test_date_mmddyyyy():
    analysis = analyze("01151987")
    est = DateEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # Without separator: 200 * 365 = 73,000
    assert result.guess_number == 200 * 365


def test_date_with_separator():
    analysis = analyze("01/15/1987")
    est = DateEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # With separator: 200 * 365 * 4 = 292,000
    assert result.guess_number == 200 * 365 * 4


def test_date_no_date():
    analysis = analyze("xyzxyz")
    est = DateEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")


def test_date_yyyymmdd():
    analysis = analyze("19870115")
    est = DateEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
