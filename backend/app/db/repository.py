import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from backend.app.db.models import Dataset, Report


def save_dataset_metadata(
    db: Session,
    dataset_id: str,
    original_filename: str,
    num_rows: int,
    num_columns: int,
) -> Dataset:
    """Persist metadata for a newly uploaded dataset."""
    dataset = Dataset(
        dataset_id=dataset_id,
        original_filename=original_filename,
        num_rows=num_rows,
        num_columns=num_columns,
        uploaded_at=datetime.now(timezone.utc),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_dataset_metadata(db: Session, dataset_id: str) -> Dataset | None:
    """Retrieve metadata for a dataset by its ID, or None if not found."""
    return db.query(Dataset).filter(Dataset.dataset_id == dataset_id).first()


def save_report(db: Session, dataset_id: str, report_type: str, report_data: dict) -> Report:
    """Persist a quality or drift report, returning it with its generated report_id."""
    report = Report(
        report_id=str(uuid.uuid4()),
        dataset_id=dataset_id,
        report_type=report_type,
        report_data=report_data,
        created_at=datetime.now(timezone.utc),
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> Report | None:
    """Retrieve a saved report by its ID, or None if not found."""
    return db.query(Report).filter(Report.report_id == report_id).first()