from pathlib import Path

# Root of the project (three levels up from this file: core -> app -> backend -> project root)
PROJECT_ROOT = Path(__file__).resolve().parents[3]

UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {".csv"}

# Ensure the uploads folder exists at startup
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
# --- Cleanup ---
# Uploaded files older than this are considered eligible for cleanup.
UPLOAD_RETENTION_DAYS = 7