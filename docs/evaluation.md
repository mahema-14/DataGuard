# Evaluation Results

## Test coverage

32 automated tests across 5 test files, 90% line coverage on core services (`pytest --cov`):

| Module | Coverage |
|---|---|
| profiling_service.py | 100% |
| scoring_service.py | 93% |
| drift_service.py | 92% |
| validation_service.py | 91% |
| file_service.py | 62% |

## Validation against a known sample dataset

A 20-row sample dataset (`dataguard_sample_v1.csv`) was constructed with 9 deliberately planted issues, and every detection function was verified against the known-correct answer:

| Planted issue | Detected? |
|---|---|
| 15% missing values in `age` | ✅ Flagged as warning |
| Constant column (`plan_type`) | ✅ Flagged |
| Identifier-like column (`customer_id`, 100% unique) | ✅ Flagged as informational |
| Numeric outlier (`purchase_amount` = 999999) | ✅ Flagged, correctly not over-triggered on legitimate variance |
| Impossible negative value (`age` = -5) | ✅ Flagged as critical via user-configured rule |
| Inconsistent capitalization (`India`/`india`/`INDIA`) | ✅ Surfaced via rare-category and categorical stats |
| Rare category (`Nepal`, 1 occurrence) | ✅ Flagged |
| Mixed date formats | ✅ Visible in categorical stats |
| Overall quality score | 95.89/100, hand-verified to match the weighted formula exactly |

## Drift detection validation

A second sample (`dataguard_sample_v2.csv`) was constructed with known schema and distribution changes:

| Change | Detected? |
|---|---|
| Column added (`referral_source`) | ✅ |
| Column removed (`plan_type`) | ✅ |
| `purchase_amount` distribution shifted 2.5–4x | ✅ Flagged via KS test (p=0.0) and 90% mean change |
| `age` distribution deliberately unchanged | ✅ Correctly not flagged (no false positive) |
| New category (`Japan` in `country`) | ✅ Detected and reported separately from the drift flag |
| Identifier-like columns (`email`, `signup_date`, `customer_id`) | ✅ Correctly excluded from categorical drift to avoid meaningless 100%-divergence noise |