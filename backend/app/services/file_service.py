import uuid
from pathlib import Path
import time

from backend.app.core.config import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_MB, UPLOAD_DIR


class InvalidFileError(Exception):
    """Raised when an uploaded file fails validation."""


def validate_filename(filename: str) -> None:
    """Ensure the file has an allowed extension. Raises InvalidFileError if not."""
    extension = Path(filename).suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidFileError(
            f"Unsupported file type '{extension}'. Only CSV files are allowed."
        )


def validate_file_size(size_bytes: int) -> None:
    """Ensure the file does not exceed the configured size limit."""
    max_bytes = MAX_FILE_SIZE_MB * 1024 * 1024
    if size_bytes > max_bytes:
        raise InvalidFileError(
            f"File is too large ({size_bytes / (1024 * 1024):.2f} MB). "
            f"Maximum allowed size is {MAX_FILE_SIZE_MB} MB."
        )
    if size_bytes == 0:
        raise InvalidFileError("The uploaded file is empty.")


def generate_safe_filename(original_filename: str) -> tuple[str, str]:
    """
    Generate a unique dataset ID and a safe filename for storage.

    We never trust the user-provided filename for constructing file paths,
    since it could contain path traversal characters (e.g. '../../etc/passwd').
    Instead we generate our own ID and only keep the extension.
    """
    dataset_id = str(uuid.uuid4())
    extension = Path(original_filename).suffix.lower()
    safe_filename = f"{dataset_id}{extension}"
    return dataset_id, safe_filename


def cleanup_old_uploads(retention_days: int | None = None) -> list[str]:
    """
    Delete uploaded files older than the retention period.
    Returns the list of filenames that were deleted.

    This does not touch the database -- dataset metadata rows for
    deleted files are intentionally left in place as a historical
    record, even though their underlying file is gone.
    """
    from backend.app.core.config import UPLOAD_RETENTION_DAYS

    days = retention_days if retention_days is not None else UPLOAD_RETENTION_DAYS
    cutoff_seconds = days * 24 * 60 * 60
    now = time.time()
    deleted: list[str] = []

    for file_path in UPLOAD_DIR.glob("*.csv"):
        file_age_seconds = now - file_path.stat().st_mtime
        if file_age_seconds > cutoff_seconds:
            file_path.unlink()
            deleted.append(file_path.name)

    return deleted