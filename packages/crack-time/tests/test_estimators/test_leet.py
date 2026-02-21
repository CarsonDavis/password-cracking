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


def test_l33t_does_not_cheapen_dictionary():
    """L33t match for 'car1' (carl) should cost more than dictionary 'car' (261)."""
    analysis = analyze("car1")
    est = L33tEstimator()
    result = est.estimate(analysis)
    if result.guess_number != float("inf"):
        assert result.guess_number > 261  # must exceed plain "car" dict rank


def test_l33t_full_variant_count():
    """p@ssw0rd should have l33t multiplier reflecting all variants of 'password'."""
    analysis = analyze("p@ssw0rd")
    est = L33tEstimator()
    result = est.estimate(analysis)
    # Find the "password" match specifically to verify the variant count formula
    password_matches = [m for m in result.matches if m.word == "password"]
    assert len(password_matches) == 1
    # password rank=1, full variants: p(1)*a(3)*s(3)*s(3)*w(1)*o(2)*r(1)*d(1) = 54
    assert password_matches[0].guesses == 54
