"""Tests for the mask estimator."""

from crack_time.analysis.analyzer import analyze
from crack_time.estimators.mask import MaskEstimator, char_to_mask_class, mask_guesses


def test_mask_class_detection():
    assert char_to_mask_class("a") == "?l"
    assert char_to_mask_class("A") == "?u"
    assert char_to_mask_class("5") == "?d"
    assert char_to_mask_class("!") == "?s"


def test_mask_guesses_simple():
    # "Ab1!" -> ?u?l?d?s -> 26*26*10*33 = 222,768
    assert mask_guesses("Ab1!") == 26 * 26 * 10 * 33


def test_mask_estimator():
    analysis = analyze("aaa111")
    est = MaskEstimator()
    result = est.estimate(analysis)
    # ?l?l?l?d?d?d -> 26^3 * 10^3 = 17,576,000
    assert result.guess_number <= 26 ** 3 * 10 ** 3


def test_mask_empty():
    analysis = analyze("")
    est = MaskEstimator()
    result = est.estimate(analysis)
    assert result.guess_number == float("inf")


def test_mask_common_pattern():
    """Common mask patterns should get lower guess counts due to priority."""
    analysis = analyze("abcdef")  # ?l?l?l?l?l?l - very common mask
    est = MaskEstimator()
    result = est.estimate(analysis)
    # Should be less than raw keyspace due to priority ordering
    assert result.guess_number <= 26 ** 6
