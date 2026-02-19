"""POST /api/compare/* — Comparison endpoints (UC-3, UC-4, UC-5)."""

from fastapi import APIRouter, HTTPException

from crack_time.simulator import estimate_password
from crack_time_api.schemas import (
    CompareAlgorithmsRequest,
    CompareAttackersRequest,
    ComparePasswordsRequest,
    EstimateResponse,
    simulation_to_response,
)

router = APIRouter(prefix="/compare")


@router.post("/passwords", response_model=list[EstimateResponse])
def compare_passwords(req: ComparePasswordsRequest):
    """UC-3: Compare multiple passwords side by side."""
    if len(req.passwords) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 passwords to compare")
    results = []
    for pw in req.passwords:
        try:
            r = estimate_password(pw, req.algorithm, req.hardware_tier)
            results.append(simulation_to_response(r))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error for '{pw}': {e}")
    return results


@router.post("/algorithms", response_model=list[EstimateResponse])
def compare_algorithms(req: CompareAlgorithmsRequest):
    """UC-4: Same password across different hash algorithms."""
    if len(req.algorithms) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 algorithms to compare")
    results = []
    for algo in req.algorithms:
        try:
            r = estimate_password(req.password, algo, req.hardware_tier)
            results.append(simulation_to_response(r))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error for algorithm '{algo}': {e}")
    return results


@router.post("/attackers", response_model=list[EstimateResponse])
def compare_attackers(req: CompareAttackersRequest):
    """UC-5: Same password across different hardware tiers."""
    if len(req.hardware_tiers) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 hardware tiers to compare")
    results = []
    for tier in req.hardware_tiers:
        try:
            r = estimate_password(req.password, req.algorithm, tier)
            results.append(simulation_to_response(r))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error for tier '{tier}': {e}")
    return results
