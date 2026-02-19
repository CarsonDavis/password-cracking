"""Tests for the hardware calculator."""

import pytest

from crack_time.hardware.calculator import crack_time_seconds, effective_hash_rate
from crack_time.hardware.hash_rates import HASH_RATES_PER_GPU, resolve_hash_rate
from crack_time.hardware.tiers import HARDWARE_TIERS, get_tier


def test_hash_rate_lookup():
    assert resolve_hash_rate("md5") == 164_100_000_000
    assert resolve_hash_rate("bcrypt_cost12") == 1437


def test_hash_rate_bcrypt_derivation():
    """Derive bcrypt cost from cost=5 baseline."""
    base = resolve_hash_rate("bcrypt_cost5")
    assert base == 184_000
    # cost 10 = 184000 / 2^5 = 5750
    assert resolve_hash_rate("bcrypt_cost10") == 5750
    # cost 14 = 184000 / 2^9 = 359.375
    assert abs(resolve_hash_rate("bcrypt_cost14") - 359.375) < 1


def test_hash_rate_unknown():
    with pytest.raises(ValueError, match="Unknown algorithm"):
        resolve_hash_rate("unknown_hash")


def test_hardware_tier_lookup():
    tier = get_tier("consumer")
    assert tier["multiplier"] == 1.0
    assert tier["description"] == "RTX 4090"


def test_hardware_tier_unknown():
    with pytest.raises(ValueError, match="Unknown hardware tier"):
        get_tier("nonexistent")


def test_crack_time_seconds_simple():
    """1 million guesses at bcrypt_cost12 on consumer hardware."""
    rate = resolve_hash_rate("bcrypt_cost12")  # 1437 H/s
    ct = crack_time_seconds(1_000_000, "bcrypt_cost12", "consumer")
    expected = 1_000_000 / 1437
    assert abs(ct - expected) < 0.01


def test_crack_time_seconds_large_rig():
    """Large rig = 7x consumer."""
    ct_consumer = crack_time_seconds(1_000_000, "bcrypt_cost12", "consumer")
    ct_rig = crack_time_seconds(1_000_000, "bcrypt_cost12", "large_rig")
    assert abs(ct_consumer / ct_rig - 7.0) < 0.01


def test_effective_hash_rate():
    rate = effective_hash_rate("bcrypt_cost12", "consumer")
    assert rate == 1437 * 1.0

    rate_rig = effective_hash_rate("bcrypt_cost12", "large_rig")
    assert rate_rig == 1437 * 7.0


def test_crack_time_zero_guesses():
    ct = crack_time_seconds(0, "bcrypt_cost12", "consumer")
    assert ct == 0
