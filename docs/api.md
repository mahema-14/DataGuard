# API Reference

Full interactive documentation is available at `/docs` (Swagger UI) when the backend is running. This file summarizes the main endpoints.

## `GET /health`
Health check. Returns `{"status": "ok"}`.

## `POST /datasets/upload`
Accepts a CSV file (`multipart/form-data`, field name `file`). Validates file type, size, and non-empty content. Returns dataset metadata including a generated `dataset_id`.

## `GET /datasets/{dataset_id}/profile`
Returns the full structural profile: row/column counts, missing value statistics, numeric statistics, categorical statistics.

## `GET /datasets/{dataset_id}/quality-report`
Returns detected quality issues and the overall quality score (with sub-score breakdown). Persists the report to the database and includes its `report_id`.

## `GET /datasets/{dataset_id}/column/{column_name}/values`
Returns raw values for a single numeric column, scoped narrowly for charting purposes — not a general data-export endpoint.

## `POST /drift/compare`
Query params: `baseline_dataset_id`, `current_dataset_id`. Returns schema comparison, numerical drift results, categorical drift results, and a summary.

## Error handling
- `400` — invalid file (wrong type, empty, unparseable)
- `404` — dataset or column not found
- `422` — request validation error (FastAPI/Pydantic default)