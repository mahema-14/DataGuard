from fastapi import FastAPI

from backend.app.api.routes_datasets import router as datasets_router
from backend.app.api.routes_drift import router as drift_router

app = FastAPI(title="DataGuard API")
app.include_router(datasets_router)
app.include_router(drift_router)


@app.get("/health")
def health_check() -> dict[str, str]:
    """Simple endpoint to confirm the API is running."""
    return {"status": "ok"}