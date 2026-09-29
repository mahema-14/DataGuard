from datetime import datetime, timezone
from backend.app.services.profiling_service import profile_dataset
from backend.app.services.validation_service import run_all_checks
from backend.app.services.scoring_service import calculate_quality_score
from sqlalchemy.orm import Session
from fastapi import Depends

from backend.app.db.database import get_db
from backend.app.db.repository import save_dataset_metadata, save_report

import pandas as pd
from fastapi import APIRouter, UploadFile, File, HTTPException

from backend.app.core.config import UPLOAD_DIR
from backend.app.services.file_service import (
    InvalidFileError,
    validate_filename,
    validate_file_size,
    generate_safe_filename,
)

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> dict:
    """Accept a CSV upload, validate it, and store it safely on disk."""

    try:
        validate_filename(file.filename)
    except InvalidFileError as e:
        raise HTTPException(status_code=400, detail=str(e))

    contents = await file.read()
    try:
        validate_file_size(len(contents))
    except InvalidFileError as e:
        raise HTTPException(status_code=400, detail=str(e))

    dataset_id, safe_filename = generate_safe_filename(file.filename)
    destination = UPLOAD_DIR / safe_filename
    destination.write_bytes(contents)

    try:
        df = pd.read_csv(destination)
    except Exception:
        raise HTTPException(status_code=400, detail="File could not be parsed as a valid CSV.")

    save_dataset_metadata(
        db=db,
        dataset_id=dataset_id,
        original_filename=file.filename,
        num_rows=len(df),
        num_columns=len(df.columns),
    )

    return {
        "dataset_id": dataset_id,
        "original_filename": file.filename,
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/{dataset_id}/profile")
def get_dataset_profile(dataset_id: str) -> dict:
    """Return the full profile for a previously uploaded dataset."""
    file_path = UPLOAD_DIR / f"{dataset_id}.csv"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found.")

    df = pd.read_csv(file_path)
    return profile_dataset(df)

@router.get("/{dataset_id}/column/{column_name}/values")
def get_column_values(dataset_id: str, column_name: str) -> dict:
    """
    Return raw values for a single numeric column, for charting purposes.
    Only exposes one column at a time, not the full dataset, to keep this
    endpoint narrowly scoped to its charting use case.
    """
    file_path = UPLOAD_DIR / f"{dataset_id}.csv"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found.")

    df = pd.read_csv(file_path)

    if column_name not in df.columns:
        raise HTTPException(status_code=404, detail=f"Column '{column_name}' not found.")

    if not pd.api.types.is_numeric_dtype(df[column_name]):
        raise HTTPException(status_code=400, detail=f"Column '{column_name}' is not numeric.")

    values = df[column_name].dropna().tolist()

    return {"column": column_name, "values": values}

@router.get("/{dataset_id}/quality-report")
def get_quality_report(dataset_id: str, db: Session = Depends(get_db)) -> dict:
    """Return detected quality issues and the overall quality score."""
    file_path = UPLOAD_DIR / f"{dataset_id}.csv"

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Dataset not found.")

    df = pd.read_csv(file_path)
    profile = profile_dataset(df)
    issues = run_all_checks(df, profile)
    score = calculate_quality_score(df, profile, issues)

    result = {
        "dataset_id": dataset_id,
        "num_issues": len(issues),
        "issues": issues,
        "quality_score": score,
    }

    saved_report = save_report(db, dataset_id, "quality", result)
    result["report_id"] = saved_report.report_id

    return result