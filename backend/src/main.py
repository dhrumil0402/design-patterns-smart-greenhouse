from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from scalar_fastapi import get_scalar_api_reference

from infrastructure.settings import get_settings
from interfaces.api.health import router as health_router

settings = get_settings()

app = FastAPI(
    title="Smart Greenhouse API",
    description="Backend API for the Smart Greenhouse platform.",
    version="0.1.0",
    # Built-in Swagger / ReDoc are disabled on purpose — Scalar (below) is
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