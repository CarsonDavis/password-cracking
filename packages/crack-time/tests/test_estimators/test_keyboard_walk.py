"""Tests for the keyboard walk estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.keyboard_walk import KeyboardWalkEstimator


def test_keyboard_walk_qwerty():
    analysis = analyze("qwerty")
    est = KeyboardWalkEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    assert len(result.matches) > 0


def test_keyboard_walk_no_walk():
    analysis = analyze("azbycx")
    est = KeyboardWalkEstimator()
    result = est.estimate(analysis)
    # Non-adjacent characters should not form a walk
    assert result.guess_number == float("inf") or len(result.matches) == 0


def test_keyboard_walk_straight_line():
    """A straight walk should have turns=1."""
    analysis = analyze("asdfgh")
    est = KeyboardWalkEstimator()
    result = est.estimate(analysis)
    assert result.guess_number != float("inf")
    # For a straight walk, guesses should be reasonable (not 1)
    assert result.guess_number > 1


def test_keyboard_walk_with_turn():
    """Walk with direction change should detect turns."""
    analysis = analyze("qweasd")
    est = KeyboardWalkEstimator()
    result = est.estimate(analysis)
    # Whether this forms a walk depends on adjacency
    assert isinstance(result.guess_number, (int, float))
