"""Hash rate lookup table and bcrypt cost derivation."""

from __future__ import annotations

HASH_RATES_PER_GPU: dict[str, float] = {
    "md5": 164_100_000_000,
    "sha1": 50_638_700_000,
    "sha256": 21_975_500_000,
    "sha512": 7_483_400_000,
    "ntlm": 288_500_000_000,
    "bcrypt_cost5": 184_000,
    "bcrypt_cost10": 5_750,
    "bcrypt_cost12": 1_437,
    "scrypt_default": 7_126,
    "argon2id_64m_t3": 600,
    "pbkdf2_sha256": 8_865_700,
    "wpa_wpa2": 2_533_300,
}


def resolve_hash_rate(algorithm: str) -> float:
    """Look up base hash rate. For bcrypt with arbitrary cost, derive from cost=5."""
    if algorithm in HASH_RATES_PER_GPU:
        return HASH_RATES_PER_GPU[algorithm]

    if algorithm.startswith("bcrypt_cost"):
        cost = int(algorithm.removeprefix("bcrypt_cost"))
        return HASH_RATES_PER_GPU["bcrypt_cost5"] / (2 ** (cost - 5))

    supported = sorted(HASH_RATES_PER_GPU.keys())
    raise ValueError(
        f"Unknown algorithm: '{algorithm}'. "
        f"Supported: {', '.join(supported)}. "
        f"For bcrypt, use 'bcrypt_costN' with any cost N."
    )
