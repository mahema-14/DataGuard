import pandas as pd
from fastapi import APIRouter, HTTPException

from backend.app.core.config import UPLOAD_DIR
from backend.app.services.drift_service import compare_datasets

router = APIRouter(prefix="/drift", tags=["drift"])


@router.post("/compare")
def compare(baseline_dataset_id: str, current_dataset_id: str) -> dict:
    """Compare a baseline dataset against a current dataset for drift."""
    baseline_path = UPLOAD_DIR / f"{baseline_dataset_id}.csv"
    current_path = UPLOAD_DIR / f"{current_dataset_id}.csv"

    if not baseline_path.exists():
        raise HTTPException(status_code=404, detail="Baseline dataset not found.")
    if not current_path.exists():
        raise HTTPException(status_code=404, detail="Current dataset not found.")

    baseline_df = pd.read_csv(baseline_path)
    current_df = pd.read_csv(current_path)

    return compare_datasets(baseline_df, current_df)