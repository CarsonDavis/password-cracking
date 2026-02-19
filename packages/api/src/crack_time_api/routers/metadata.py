"""GET /api/metadata — Available algorithms and hardware tiers (UC-6)."""

from fastapi import APIRouter

from crack_time_api.schemas import MetadataResponse, get_metadata

router = APIRouter()


@router.get("/metadata", response_model=MetadataResponse)
def metadata():
    return get_metadata()
