"""POST /api/batch — Batch password audit (UC-2)."""

from fastapi import APIRouter, HTTPException

from crack_time.simulator import estimate_password
from crack_time_api.schemas import (
    BatchPasswordResult,
    BatchRequest,
    BatchResponse,
    BatchSummary,
    sanitize_inf,
)

router = APIRouter()


@router.post("/batch", response_model=BatchResponse)
def batch(req: BatchRequest):
    if not req.passwords:
        raise HTTPException(status_code=400, detail="passwords list cannot be empty")

    results = []
    for pw in req.passwords:
        try:
            r = estimate_password(pw, req.algorithm, req.hardware_tier)
            results.append(r)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=f"Error for '{pw}': {e}")

    # Build summary
    rating_dist = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
    attack_dist: dict[str, int] = {}
    for r in results:
        rating_dist[r.rating] = rating_dist.get(r.rating, 0) + 1
        attack_dist[r.winning_attack] = attack_dist.get(r.winning_attack, 0) + 1

    crack_times = sorted(r.crack_time_seconds for r in results)
    median_ct = crack_times[len(crack_times) // 2]

    password_results = [
        BatchPasswordResult(
            password=r.password,
            crack_time_seconds=sanitize_inf(r.crack_time_seconds),
            crack_time_display=r.crack_time_display,
            rating=r.rating,
            rating_label=r.rating_label,
            winning_attack=r.winning_attack,
            guess_number=sanitize_inf(r.guess_number),
        )
        for r in results
    ]

    return BatchResponse(
        total_passwords=len(results),
        summary=BatchSummary(
            median_crack_time_seconds=median_ct,
            rating_distribution=rating_dist,
            winning_attack_distribution=attack_dist,
        ),
        passwords=password_results,
    )
