"""
Central configuration for all data quality check thresholds.

Keeping these in one file means we can tune sensitivity without
hunting through check logic, and makes the reasoning behind each
number explicit and easy to justify in an interview.
"""

# --- Missing values ---
# Below this, missing values are common and usually not alarming.
# Above this, it likely affects model reliability enough to flag.
HIGH_MISSING_WARNING_PCT = 10.0
HIGH_MISSING_CRITICAL_PCT = 40.0

# --- Cardinality ---
# A column where almost every value is unique behaves like an identifier,
# not a feature. 95% is a common practical cutoff used in industry tools.
HIGH_CARDINALITY_UNIQUE_PCT = 95.0

# --- Rare categories ---
# A category appearing in less than 1% of rows is often too sparse
# for a model to learn a reliable pattern from.
RARE_CATEGORY_PCT = 1.0

# --- Outliers ---
# Values beyond this many standard deviations from the mean are
# flagged as statistical outliers. 3 is a widely used default
# (99.7% of normally-distributed data falls within 3 std devs).
OUTLIER_STD_THRESHOLD = 3.0

# --- Duplicates ---
# Any duplicate rows above this percentage of the dataset are
# worth flagging as a potential data collection issue.
DUPLICATE_WARNING_PCT = 1.0
# --- Quality scoring weights ---
# These weights determine how much each sub-score contributes to the
# overall 0-100 quality score. They are a practical heuristic, not a
# universal scientific measurement, and are intentionally configurable
# in one place so they can be tuned without touching scoring logic.
SCORE_WEIGHTS = {
    "completeness": 0.35,
    "validity": 0.25,
    "uniqueness": 0.20,
    "consistency": 0.10,
    "outlier_health": 0.10,
}
# --- Drift detection ---
# A KS test p-value below this suggests the two distributions are
# statistically different (standard significance level).
DRIFT_KS_PVALUE_THRESHOLD = 0.05

# A relative change in mean beyond this percentage is flagged even if
# the KS test doesn't trigger, since KS tests can miss shifts in small samples.
DRIFT_MEAN_RELATIVE_CHANGE_PCT = 20.0

# Jensen-Shannon divergence above this suggests meaningfully different
# categorical distributions. Ranges from 0 (identical) to 1 (completely different).
DRIFT_JS_DIVERGENCE_THRESHOLD = 0.10
# --- Drift-specific cardinality exclusion ---
# For categorical drift specifically, we use a stricter (lower) cardinality
# cutoff than HIGH_CARDINALITY_UNIQUE_PCT. Even a column at 80-95% unique
# (e.g. email, signup_date) will appear to "completely drift" between any
# two samples just because the specific values differ, which is noise,
# not signal, for drift purposes.
DRIFT_CATEGORICAL_CARDINALITY_EXCLUSION_PCT = 80.0