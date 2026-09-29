# Architecture

## Overview

DataGuard follows a layered architecture with a clear separation between the API layer, business logic (services), and data access layer

```text
┌─────────────┐      HTTP       ┌──────────────┐
│  Streamlit  │ ───────────────▶│   FastAPI    │
│  Frontend   │◀─────────────── │   Backend    │
└─────────────┘      JSON       └──────┬───────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    ▼                  ▼                  ▼
             ┌───────────────┐  ┌────────────────┐  ┌────────────────┐
             │   Services    │  │    Services    │  │    Database    │
             │  (profiling,   │  │    (drift)     │  │  (SQLite via   │
             │  validation,  │  │                │  │   SQLAlchemy)  │
             │   scoring)     │  │                │  │                │
             └───────────────┘  └────────────────┘  └────────────────┘

```

## Request flow: upload → quality report

1. User uploads a CSV through Streamlit → `POST /datasets/upload`
2. `file_service` validates the file (type, size, non-empty) and generates a UUID-based filename, never trusting the user-supplied name
3. The file is saved to `data/uploads/{uuid}.csv`; metadata is persisted to SQLite via `repository.py`
4. On `GET /datasets/{id}/quality-report`:
   - `profiling_service.profile_dataset()` computes structural statistics
   - `validation_service.run_all_checks()` turns the profile into a list of issues, each with severity, explanation, and recommendation
   - `scoring_service.calculate_quality_score()` derives five weighted sub-scores and an overall 0–100 score from the profile and issues
   - The full report is persisted and returned as JSON

## Request flow: drift comparison

1. User selects two previously uploaded datasets (baseline, current)
2. `POST /drift/compare` loads both CSVs and calls `drift_service.compare_datasets()`:
   - `compare_schemas()` — added/removed columns, dtype changes, row count changes
   - `detect_numerical_drift()` — KS test + relative mean change per shared numeric column
   - `detect_categorical_drift()` — Jensen-Shannon divergence + new/removed categories, excluding high-cardinality (identifier-like) columns
3. Results are combined into a single summary indicating which columns drifted and why

## Key design decisions

- **Services never touch the database or HTTP layer directly** — they take and return plain Python data structures (DataFrames, dicts), making every function independently testable without mocking a request or a session.
- **Dataset IDs double as file paths.** Since uploaded filenames are always `{uuid}.csv`, no lookup table is needed to find a file from its ID — reducing unnecessary database dependencies for a simple case.
- **Thresholds are centralized** in `core/thresholds.py` with inline comments justifying each value, rather than scattered as magic numbers through the codebase.
- **A stricter cardinality threshold is used for drift than for general quality checks** (80% vs. 95%), because near-unique columns like `email` or `signup_date` produce meaningless "100% drift" noise between any two independent samples — a distinction discovered and fixed during development via automated testing.
- **JSON columns in SQLite** store full report payloads rather than a normalized relational schema, trading query flexibility for simplicity, appropriate for a single-user local tool.

## Data flow diagram: quality scoring             

```text
Raw CSV
 │
 ▼
 profile_dataset() ──▶ missing_stats, numeric_stats, categorical_stats
 │
 ▼
 run_all_checks() ──▶ list of issues (severity, explanation, recommendation)
 │
 ▼
 calculate_quality_score() ──▶ 5 sub-scores ──▶ weighted sum ──▶ overall score (0-100)
```
