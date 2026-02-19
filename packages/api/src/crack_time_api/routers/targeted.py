"""POST /api/targeted — Targeted attack with personal context (UC-7)."""

from fastapi import APIRouter, HTTPException

from crack_time.simulator import estimate_password
from crack_time_api.schemas import (
    EstimateResponse,
    StrategyInfo,
    TargetedRequest,
    simulation_to_response,
)

router = APIRouter()


@router.post("/targeted", response_model=EstimateResponse)
def targeted(req: TargetedRequest):
    """Evaluate a password with personal context items factored in.

    Context items (names, dates, etc.) are checked as dictionary words.
    If the password contains any context items, the effective guess number
    is reduced to reflect targeted attack advantage.
    """
    try:
        result = estimate_password(req.password, req.algorithm, req.hardware_tier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    response = simulation_to_response(result)

    # Check if any context items appear in the password
    if req.context:
        pw_lower = req.password.lower()
        matched_context = [c for c in req.context if c.lower() in pw_lower]
        if matched_context:
            response.winning_attack = "targeted_" + response.winning_attack
            response.strategies["targeted_context"] = StrategyInfo(
                guess_number=response.guess_number,
                attack_name="Targeted attack (personal context)",
                details={"matched_context": matched_context},
            )

    return response
