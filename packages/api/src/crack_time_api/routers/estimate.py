"""POST /api/estimate — Single password evaluation (UC-1)."""

from fastapi import APIRouter, HTTPException

from crack_time.simulator import estimate_password
from crack_time_api.schemas import EstimateRequest, EstimateResponse, simulation_to_response

router = APIRouter()


@router.post("/estimate", response_model=EstimateResponse)
def estimate(req: EstimateRequest):
    try:
        result = estimate_password(req.password, req.algorithm, req.hardware_tier)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return simulation_to_response(result)
