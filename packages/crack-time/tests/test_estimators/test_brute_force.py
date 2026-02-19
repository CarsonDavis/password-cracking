"""Tests for the brute force estimator."""

from crack_time.estimators.brute_force import BruteForceEstimator
from crack_time.types import PasswordAnalysis


def test_brute_force_empty():
    est = BruteForceEstimator()
    analysis = PasswordAnalysis(password="", length=0, cardinality=0)
    result = est.estimate(analysis)
    assert result.guess_number == 0


def test_brute_force_lowercase():
    est = BruteForceEstimator()
    analysis = PasswordAnalysis(
        password="abcd", length=4,
        charsets={"lower"}, cardinality=26,
    )
    result = est.estimate(analysis)
    assert result.guess_number == 26 ** 4  # 456,976


def test_brute_force_all_charsets():
    est = BruteForceEstimator()
    analysis = PasswordAnalysis(
        password="aB3!", length=4,
        charsets={"lower", "upper", "digit", "special"}, cardinality=95,
    )
    result = est.estimate(analysis)
    assert result.guess_number == 95 ** 4  # 81,450,625


def test_brute_force_digits_only():
    est = BruteForceEstimator()
    analysis = PasswordAnalysis(
        password="1234", length=4,
        charsets={"digit"}, cardinality=10,
    )
    result = est.estimate(analysis)
    assert result.guess_number == 10 ** 4  # 10,000


def test_brute_force_special_only():
    """Spaces are special chars, cardinality=33."""
    est = BruteForceEstimator()
    analysis = PasswordAnalysis(
        password="   ", length=3,
        charsets={"special"}, cardinality=33,
    )
    result = est.estimate(analysis)
    assert result.guess_number == 33 ** 3  # 35,937
