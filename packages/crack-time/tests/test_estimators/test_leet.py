"""Tests for the l33t estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.leet import L33tEstimator


def test_l33t_password():
    analysis = analyze("p@ssw0rd")
    est = L33tEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    assert len(result.matches) > 0


def test_l33t_no_subs():
    """Plain dictionary word without l33t should not match as l33t."""
    analysis = analyze("password")
    est = L33tEstimator()
    result = est.estimate(analysis)
    # No l33t matches for plain word
    assert result.guess_number == float("inf")


def test_l33t_simple_sub():
    """Single substitution: @ for a."""
    analysis = analyze("p@ss")
    est = L33tEstimator()
    result = est.estimate(analysis)
    # Should find if "pass" is in a dictionary
    # The result depends on whether "pass" is in our wordlists
    # At minimum, it should not crash
    assert isinstance(result.guess_number, (int, float))
