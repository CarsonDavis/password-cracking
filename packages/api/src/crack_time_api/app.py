"""FastAPI application factory and entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from crack_time_api.routers import batch, compare, estimate, metadata, targeted


def create_app() -> FastAPI:
    app = FastAPI(
        title="Password Crack-Time Simulator",
        description="API for estimating password crack times across hash algorithms and hardware tiers.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(estimate.router, prefix="/api", tags=["estimate"])
    app.include_router(batch.router, prefix="/api", tags=["batch"])
    app.include_router(compare.router, prefix="/api", tags=["compare"])
    app.include_router(metadata.router, prefix="/api", tags=["metadata"])
    app.include_router(targeted.router, prefix="/api", tags=["targeted"])

    return app


app = create_app()


def run():
    import uvicorn
    uvicorn.run("crack_time_api.app:app", host="0.0.0.0", port=8000, reload=True)
