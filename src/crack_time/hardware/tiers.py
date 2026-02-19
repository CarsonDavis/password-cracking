"""Hardware tier definitions with multipliers."""

from __future__ import annotations

HARDWARE_TIERS: dict[str, dict] = {
    "budget": {"description": "GTX 1080 Ti", "multiplier": 0.19},
    "consumer": {"description": "RTX 4090", "multiplier": 1.0},
    "enthusiast": {"description": "RTX 5090", "multiplier": 1.34},
    "small_rig": {"description": "4x RTX 4090", "multiplier": 3.6},
    "large_rig": {"description": "8x RTX 4090", "multiplier": 7.0},
    "dedicated": {"description": "14x RTX 4090", "multiplier": 12.2},
    "well_funded": {"description": "~100 GPUs", "multiplier": 85.0},
    "nation_state": {"description": "10K+ GPUs", "multiplier": 8500.0},
}


def get_tier(name: str) -> dict:
    """Look up a hardware tier by name."""
    if name not in HARDWARE_TIERS:
        supported = sorted(HARDWARE_TIERS.keys())
        raise ValueError(
            f"Unknown hardware tier: '{name}'. "
            f"Supported: {', '.join(supported)}"
        )
    return HARDWARE_TIERS[name]
