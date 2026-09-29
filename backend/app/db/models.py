from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, DateTime, JSON

from backend.app.db.database import Base


class Dataset(Base):
    """Metadata for an uploaded dataset."""
    __tablename__ = "datasets"

    dataset_id = Column(String, primary_key=True)
    original_filename = Column(String, nullable=False)
    num_rows = Column(Integer, nullable=False)
    num_columns = Column(Integer, nullable=False)
    uploaded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class Report(Base):
    """A saved quality or drift report for a dataset."""
    __tablename__ = "reports"

    report_id = Column(String, primary_key=True)
    dataset_id = Column(String, nullable=False)
    report_type = Column(String, nullable=False)  # "quality" or "drift"
    report_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))