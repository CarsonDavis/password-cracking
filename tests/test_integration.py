"""Integration tests: full pipeline on reference passwords."""

from crack_time.simulator import estimate_password


def test_empty_password():
    r = estimate_password("")
    assert r.guess_number == 0
    assert r.crack_time_seconds == 0
    assert r.rating == 0


def test_password_rank_1():
    r = estimate_password("password")
    assert r.guess_number == 1
    assert r.rating == 0
    assert "dictionary" in r.winning_attack.lower() or r.winning_attack == "dictionary"


def test_dragon_dictionary():
    r = estimate_password("dragon")
    assert r.guess_number < 100  # Should have a low rank
    assert r.rating == 0


def test_aaaaaa_repeat():
    r = estimate_password("aaaaaa")
    # Repeat: base_guesses(a) = 26, count = 6 -> 156
    assert r.guess_number <= 156
    assert r.rating == 0


def test_abcdefgh_sequence():
    r = estimate_password("abcdefgh")
    # Sequence estimator should find this
    assert r.guess_number < 1000
    assert r.rating == 0


def test_date_01151987():
    r = estimate_password("01151987")
    # Date: 200 * 365 = 73,000
    assert r.guess_number <= 73000
    assert r.rating == 0


def test_random_password():
    """Truly random password should fall back to brute force or mask."""
    r = estimate_password("8j$kL2!nQ")
    assert r.guess_number > 1_000_000_000  # Should be large
    assert r.rating >= 2  # At least FAIR


def test_qwerty123_decomposition():
    r = estimate_password("qwerty123")
    # Should decompose into dictionary/keyboard + sequence
    assert r.guess_number < 10000
    assert r.rating == 0
    assert len(r.decomposition) >= 1


def test_three_spaces():
    r = estimate_password("   ")
    # Repeat finds: base_guesses(space) = 33, count = 3 -> 99
    # Brute force: 33^3 = 35937
    # Repeat wins
    assert r.guess_number <= 35937
    assert r.rating == 0


def test_different_algorithms():
    """Same password, different hash algorithms should give different crack times."""
    r_bcrypt = estimate_password("password123", "bcrypt_cost12", "consumer")
    r_md5 = estimate_password("password123", "md5", "consumer")
    # MD5 is ~100M times faster, so crack time should be much less
    assert r_md5.crack_time_seconds < r_bcrypt.crack_time_seconds


def test_different_hardware():
    """Same password, different hardware should give different crack times."""
    r_consumer = estimate_password("password123", "bcrypt_cost12", "consumer")
    r_rig = estimate_password("password123", "bcrypt_cost12", "large_rig")
    assert r_rig.crack_time_seconds < r_consumer.crack_time_seconds


def test_json_output_format():
    """Test that result has all expected fields."""
    r = estimate_password("test123")
    assert r.password == "test123"
    assert r.hash_algorithm == "bcrypt_cost12"
    assert r.hardware_tier == "consumer"
    assert isinstance(r.effective_hash_rate, float)
    assert isinstance(r.guess_number, (int, float))
    assert isinstance(r.crack_time_seconds, float)
    assert isinstance(r.crack_time_display, str)
    assert isinstance(r.rating, int)
    assert isinstance(r.rating_label, str)
    assert isinstance(r.winning_attack, str)
    assert isinstance(r.strategies, dict)
    assert isinstance(r.decomposition, list)


def test_invalid_algorithm():
    """Should raise ValueError for unknown algorithm."""
    import pytest
    with pytest.raises(ValueError):
        estimate_password("test", "unknown_hash")


def test_invalid_hardware():
    """Should raise ValueError for unknown hardware tier."""
    import pytest
    with pytest.raises(ValueError):
        estimate_password("test", "bcrypt_cost12", "unknown_tier")


def test_batch_of_passwords():
    """Test that multiple passwords can be evaluated without errors."""
    passwords = [
        "password", "qwerty123", "aaaaaa", "01151987",
        "abcdefgh", "8j$kL2!nQ", "dragon", "", "   ",
    ]
    for pw in passwords:
        r = estimate_password(pw)
        assert r.rating >= 0
        assert r.rating <= 4


def test_unicode_password():
    r = estimate_password("über1234")
    assert r.rating >= 0


def test_emoji_password():
    r = estimate_password("\U0001f511\U0001f512\U0001f511\U0001f512")
    assert r.rating >= 0


def test_very_long_password():
    r = estimate_password("a" * 500)
    assert r.rating >= 0


def test_whitespace_only():
    r = estimate_password("\t\n ")
    assert r.rating >= 0


def test_single_character():
    r = estimate_password("x")
    assert r.guess_number <= 95
    assert r.rating == 0


def test_null_bytes_only():
    r = estimate_password("\x00\x00\x00")
    assert r.guess_number == 0
    assert r.rating == 0
