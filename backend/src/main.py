import asyncio
import contextlib
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from infrastructure.settings import get_settings
from interfaces.api.health import router as health_router
from interfaces.api.sensors import router as sensors_router
from interfaces.api.devices import router as devices_router
from interfaces.api.locations import router as locations_router
from infrastructure.sampler_runner import sampler_loop
from interfaces.api.sampling import router as sampling_router

settings = get_settings()
@asynccontextmanager
async def lifespan(app: FastAPI):
    task = None
    if os.getenv("SAMPLER_ENABLED", "true").lower() == "true":
        task = asyncio.create_task(sampler_loop())
    try:
        yield
    finally:
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
app = FastAPI(
    title="Smart Greenhouse API",
    description="Backend API for the Smart Greenhouse platform.",
    version="0.1.0",
    lifespan=lifespan,
    # Built-in Swagger / ReDoc are disabled on purpose â€” Scalar (below) is
    # the documented API reference for this course.
    docs_url=None,
    redoc_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(sensors_router)
app.include_router(devices_router)
app.include_router(locations_router)
app.include_router(sampling_router)


@app.get("/")
def root() -> dict[str, str]:
    """Small discovery payload pointing at the API docs."""
    return {
        "service": "smart-greenhouse-api",
        "docs": "/scalar",
        "openapi": "/openapi.json",
    }


@app.get("/scalar", include_in_schema=False)
def scalar_docs():
    return get_scalar_api_reference(
        openapi_url=app.openapi_url,
        title=app.title,
    )