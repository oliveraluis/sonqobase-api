from fastapi import FastAPI

from app.api.v1.projects import router as projects_router
from app.api.v1.collections import router as collection_router

app = FastAPI(
    title="Ephemeral Mongo MVP",
    version="1.0.0",
)

app.include_router(
    projects_router,
    prefix="/api/v1/projects",
    tags=["Projects"],
)

app.include_router(
    collection_router,
    prefix="/api/v1/collections",
    tags=["Collections"],
)


@app.get("/api/v1/health")
def health() -> dict:
    return {"status": "ok"}

