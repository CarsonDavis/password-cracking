"""Tests for the full analyzer pipeline."""

from crack_time.analysis.analyzer import analyze
from crack_time.types import (
    DateMatch,
    DictionaryMatch,
    KeyboardWalkMatch,
    L33tMatch,
    RepeatMatch,
    SequenceMatch,
)


def test_analyze_empty_password():
    result = analyze("")
    assert result.length == 0
    assert result.cardinality == 0
    assert result.matches == []


def test_analyze_password_charsets():
    result = analyze("aB3!")
    assert "lower" in result.charsets
    assert "upper" in result.charsets
    assert "digit" in result.charsets
    assert "special" in result.charsets
    assert result.cardinality == 95  # 26+26+10+33


def test_analyze_detects_dictionary_match():
    result = analyze("password")
    dict_matches = [m for m in result.matches if isinstance(m, DictionaryMatch)]
    assert len(dict_matches) > 0
    # "password" should have rank 1 in common_passwords
    full_matches = [m for m in dict_matches if m.word == "password" and m.i == 0 and m.j == 7]
    assert len(full_matches) > 0
    assert any(m.rank == 1 for m in full_matches)


def test_analyze_detects_sequence():
    result = analyze("abcdefgh")
    seq_matches = [m for m in result.matches if isinstance(m, SequenceMatch)]
    assert len(seq_matches) > 0
    full_seq = [m for m in seq_matches if m.i == 0 and m.j >= 7]
    assert len(full_seq) > 0
    assert full_seq[0].ascending is True


def test_analyze_detects_date():
    result = analyze("01151987")
    date_matches = [m for m in result.matches if isinstance(m, DateMatch)]
    assert len(date_matches) > 0
    # Should detect month=1, day=15 for MMDDYYYY parsing
    mmdd = [m for m in date_matches if m.month == 1 and m.day == 15]
    assert len(mmdd) > 0


def test_analyze_detects_repeat():
    result = analyze("aaaaaa")
    repeat_matches = [m for m in result.matches if isinstance(m, RepeatMatch)]
    assert len(repeat_matches) > 0
    assert any(m.base_token == "a" for m in repeat_matches)


def test_analyze_detects_keyboard_walk():
    result = analyze("qwerty")
    spatial_matches = [m for m in result.matches if isinstance(m, KeyboardWalkMatch)]
    assert len(spatial_matches) > 0
    assert any(m.graph == "qwerty" for m in spatial_matches)


def test_analyze_detects_l33t():
    result = analyze("p@ssw0rd")
    l33t_matches = [m for m in result.matches if isinstance(m, L33tMatch)]
    assert len(l33t_matches) > 0
    assert any(m.word == "password" for m in l33t_matches)


def test_analyze_null_bytes_stripped():
    result = analyze("pass\x00word")
    # Null bytes stripped, so treated as "password"
    assert result.password == "password"
    assert result.length == 8


def test_analyze_digit_only():
    result = analyze("123456")
    assert result.charsets == {"digit"}
    assert result.cardinality == 10


def test_analyze_mixed_patterns():
    """Test a password with multiple detectable patterns."""
    result = analyze("dragon123")
    dict_matches = [m for m in result.matches if isinstance(m, DictionaryMatch)]
    assert any(m.word == "dragon" for m in dict_matches)
