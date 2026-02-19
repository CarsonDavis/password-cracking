"""Pydantic request/response models for the API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from crack_time.hardware.hash_rates import HASH_RATES_PER_GPU
from crack_time.hardware.tiers import HARDWARE_TIERS


# --- Request schemas ---


class EstimateRequest(BaseModel):
    password: str
    algorithm: str = "bcrypt_cost12"
    hardware_tier: str = "consumer"


class BatchRequest(BaseModel):
    passwords: list[str]
    algorithm: str = "bcrypt_cost12"
    hardware_tier: str = "consumer"


class ComparePasswordsRequest(BaseModel):
    passwords: list[str]
    algorithm: str = "bcrypt_cost12"
    hardware_tier: str = "consumer"


class CompareAlgorithmsRequest(BaseModel):
    password: str
    algorithms: list[str]
    hardware_tier: str = "consumer"


class CompareAttackersRequest(BaseModel):
    password: str
    algorithm: str = "bcrypt_cost12"
    hardware_tiers: list[str]


class TargetedRequest(BaseModel):
    password: str
    algorithm: str = "bcrypt_cost12"
    hardware_tier: str = "consumer"
    context: list[str] = Field(default_factory=list)


# --- Response schemas ---


class DecompositionSegment(BaseModel):
    segment: str
    type: str
    guesses: int
    i: int
    j: int


class StrategyInfo(BaseModel):
    guess_number: float | None = None
    attack_name: str
    details: dict = Field(default_factory=dict)


class EstimateResponse(BaseModel):
    password: str
    hash_algorithm: str
    hardware_tier: str
    effective_hash_rate: float
    guess_number: float | None = None
    crack_time_seconds: float | None = None
    crack_time_display: str
    rating: int
    rating_label: str
    winning_attack: str
    strategies: dict[str, StrategyInfo] = Field(default_factory=dict)
    decomposition: list[DecompositionSegment] = Field(default_factory=list)


class BatchPasswordResult(BaseModel):
    password: str
    crack_time_seconds: float | None = None
    crack_time_display: str
    rating: int
    rating_label: str
    winning_attack: str
    guess_number: float | None = None


class BatchSummary(BaseModel):
    median_crack_time_seconds: float
    rating_distribution: dict[int, int]
    winning_attack_distribution: dict[str, int]


class BatchResponse(BaseModel):
    total_passwords: int
    summary: BatchSummary
    passwords: list[BatchPasswordResult]


class AlgorithmOption(BaseModel):
    name: str
    rate: float


class TierOption(BaseModel):
    name: str
    description: str
    multiplier: float


class MetadataResponse(BaseModel):
    algorithms: list[AlgorithmOption]
    hardware_tiers: list[TierOption]


# --- Helpers ---


def sanitize_inf(value: int | float) -> float | None:
    """Convert float('inf') to None for JSON serialization."""
    if value == float("inf"):
        return None
    return float(value)


def simulation_to_response(result) -> EstimateResponse:
    """Convert a SimulationResult to an EstimateResponse."""
    strategies = {}
    for name, info in result.strategies.items():
        strategies[name] = StrategyInfo(
            guess_number=sanitize_inf(info["guess_number"]),
            attack_name=info["attack_name"],
            details=info.get("details", {}),
        )

    decomposition = [
        DecompositionSegment(**seg) for seg in result.decomposition
    ]

    return EstimateResponse(
        password=result.password,
        hash_algorithm=result.hash_algorithm,
        hardware_tier=result.hardware_tier,
        effective_hash_rate=result.effective_hash_rate,
        guess_number=sanitize_inf(result.guess_number),
        crack_time_seconds=sanitize_inf(result.crack_time_seconds),
        crack_time_display=result.crack_time_display,
        rating=result.rating,
        rating_label=result.rating_label,
        winning_attack=result.winning_attack,
        strategies=strategies,
        decomposition=decomposition,
    )


def get_metadata() -> MetadataResponse:
    """Build metadata response from core library constants."""
    algorithms = [
        AlgorithmOption(name=name, rate=rate)
        for name, rate in sorted(HASH_RATES_PER_GPU.items())
    ]
    tiers = [
        TierOption(name=name, description=info["description"], multiplier=info["multiplier"])
        for name, info in HARDWARE_TIERS.items()
    ]
    return MetadataResponse(algorithms=algorithms, hardware_tiers=tiers)
