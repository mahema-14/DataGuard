# DataGuard

**Intelligent Data Quality and Dataset Drift Detection Platform**

DataGuard is a web application that analyzes CSV datasets for quality issues and statistical drift between dataset versions, explaining problems in plain language rather than just reporting raw statistics.

## What it does

- **Profiles** any uploaded CSV: row/column counts, missing values, data types, numeric and categorical statistics
- **Detects quality issues**: missing values, duplicate rows, constant columns, high cardinality, rare categories, numeric outliers, and user-configurable invalid-value rules
- **Scores data quality** on a transparent 0–100 scale, broken into five weighted sub-scores (completeness, validity, uniqueness, consistency, outlier health)
- **Compares two dataset versions** for schema changes and statistical drift (KS test, Jensen-Shannon divergence, new/removed categories)
- **Explains every issue** in plain language with a concrete recommendation — not just "column X has Y% missing"

## Tech stack

- **Backend**: FastAPI, Pandas, SciPy, SQLAlchemy, SQLite
- **Frontend**: Streamlit, Plotly
- **Testing**: pytest (32 tests, 90% coverage on core services)
- **Deployment**: Docker, Docker Compose

## Quick start (Docker — recommended)

```bash
docker compose up --build
```

Then open:
- Frontend: http://localhost:8501
- API docs: http://localhost:8000/docs

## Quick start (local development)

```bash
python -m venv venv
.\venv\Scripts\Activate.ps1        # Windows
pip install -r requirements.txt

# Terminal 1
uvicorn backend.app.main:app --reload

# Terminal 2
cd frontend
streamlit run streamlit_app.py
```

## Running tests

```bash
pytest --cov=backend/app/services --cov-report=term-missing
```
## Project Structure

```text 
dataguard/
├── backend/                 # FastAPI application, services, and tests
├── frontend/                # Streamlit multi-page dashboard
├── data/
│   └── sample/              # Sample datasets with known, documented quality issues
├── docs/                    # Architecture, API, and evaluation documentation
├── docker-compose.yml       # Docker Compose configuration
└── requirements.txt         # Python dependencies
``` 

## Documentation

- [Architecture](docs/architecture.md)
- [API Reference](docs/api.md)
- [Evaluation Results](docs/evaluation.md)

## Known limitations

- No authentication or multi-user support (single-user local tool by design)
- Numeric drift/outlier statistics are computed on a per-request basis, not cached
- Quality score weights are a configurable heuristic, not a scientifically validated formula
- SQLite is used for simplicity; not intended for concurrent multi-user production use

## License

MIT