import pandas as pd
from scipy import stats
import numpy as np
from scipy.spatial.distance import jensenshannon

from backend.app.core.thresholds import DRIFT_JS_DIVERGENCE_THRESHOLD

from backend.app.core.thresholds import DRIFT_CATEGORICAL_CARDINALITY_EXCLUSION_PCT
from backend.app.core.thresholds import DRIFT_KS_PVALUE_THRESHOLD, DRIFT_MEAN_RELATIVE_CHANGE_PCT

def compare_schemas(baseline_df: pd.DataFrame, current_df: pd.DataFrame) -> dict:
    """
    Compare the column structure of two datasets.

    Returns which columns were added, removed, and which columns exist
    in both (common_columns) -- the latter is what all further drift
    checks should operate on, per the spec: "Only compare columns that
    exist in both datasets."
    """
    baseline_columns = set(baseline_df.columns)
    current_columns = set(current_df.columns)

    added_columns = sorted(current_columns - baseline_columns)
    removed_columns = sorted(baseline_columns - current_columns)
    common_columns = sorted(baseline_columns & current_columns)

    dtype_changes = []
    for column in common_columns:
        baseline_dtype = str(baseline_df[column].dtype)
        current_dtype = str(current_df[column].dtype)
        if baseline_dtype != current_dtype:
            dtype_changes.append({
                "column": column,
                "baseline_dtype": baseline_dtype,
                "current_dtype": current_dtype,
            })

    return {
        "added_columns": added_columns,
        "removed_columns": removed_columns,
        "common_columns": common_columns,
        "dtype_changes": dtype_changes,
        "baseline_row_count": len(baseline_df),
        "current_row_count": len(current_df),
        "row_count_change": len(current_df) - len(baseline_df),
    }


def detect_numerical_drift(
    baseline_df: pd.DataFrame, current_df: pd.DataFrame, common_columns: list[str]
) -> list[dict]:
    """
    Detect statistical drift in numeric columns shared between two datasets.
    Uses the KS test (distribution shape) and relative mean change (magnitude)
    as two independent signals -- either can trigger a flag, since the KS
    test can miss shifts that are obvious in the mean, and vice versa.
    """
    results = []

    for column in common_columns:
        if column not in baseline_df.columns or column not in current_df.columns:
            continue

        baseline_series = baseline_df[column].dropna()
        current_series = current_df[column].dropna()

        if not pd.api.types.is_numeric_dtype(baseline_series) or not pd.api.types.is_numeric_dtype(current_series):
            continue
        if len(baseline_series) < 2 or len(current_series) < 2:
            continue

        ks_statistic, p_value = stats.ks_2samp(baseline_series, current_series)

        baseline_mean = baseline_series.mean()
        current_mean = current_series.mean()
        if baseline_mean != 0:
            relative_mean_change_pct = round(
                abs(current_mean - baseline_mean) / abs(baseline_mean) * 100, 2
            )
        else:
            relative_mean_change_pct = None

        drift_by_ks = p_value < DRIFT_KS_PVALUE_THRESHOLD
        drift_by_mean = (
            relative_mean_change_pct is not None
            and relative_mean_change_pct > DRIFT_MEAN_RELATIVE_CHANGE_PCT
        )

        results.append({
            "column": column,
            "drift_detected": bool(drift_by_ks or drift_by_mean),
            "ks_statistic": round(float(ks_statistic), 4),
            "ks_pvalue": round(float(p_value), 4),
            "baseline_mean": round(float(baseline_mean), 2),
            "current_mean": round(float(current_mean), 2),
            "relative_mean_change_pct": relative_mean_change_pct,
            "baseline_std": round(float(baseline_series.std()), 2) if len(baseline_series) > 1 else 0.0,
            "current_std": round(float(current_series.std()), 2) if len(current_series) > 1 else 0.0,
            "explanation": (
                f"Column '{column}' shows statistically significant drift "
                f"(KS p-value={round(p_value, 4)}, mean changed by {relative_mean_change_pct}%)."
                if (drift_by_ks or drift_by_mean) else
                f"Column '{column}' shows no significant drift."
            ),
        })

    return results


def detect_categorical_drift(
    baseline_df: pd.DataFrame, current_df: pd.DataFrame, common_columns: list[str]
) -> list[dict]:
    """
    Detect drift in categorical columns shared between two datasets using
    Jensen-Shannon divergence, and separately report new/removed categories.

    Columns that are highly unique (identifier-like, e.g. customer_id) in
    either dataset are skipped -- near-100% uniqueness makes "drift" a
    meaningless concept for that column, since every value naturally
    differs between any two samples.
    """
    results = []

    for column in common_columns:
        if column not in baseline_df.columns or column not in current_df.columns:
            continue
        if pd.api.types.is_numeric_dtype(baseline_df[column]) and pd.api.types.is_numeric_dtype(current_df[column]):
            continue

        baseline_non_null = baseline_df[column].dropna()
        current_non_null = current_df[column].dropna()
        baseline_unique_pct = (
            (baseline_non_null.nunique() / len(baseline_non_null)) * 100 if len(baseline_non_null) > 0 else 0
        )
        current_unique_pct = (
            (current_non_null.nunique() / len(current_non_null)) * 100 if len(current_non_null) > 0 else 0
        )
        if (
            baseline_unique_pct >= DRIFT_CATEGORICAL_CARDINALITY_EXCLUSION_PCT
            or current_unique_pct >= DRIFT_CATEGORICAL_CARDINALITY_EXCLUSION_PCT
        ):
            continue

        baseline_counts = baseline_non_null.value_counts(normalize=True)
        current_counts = current_non_null.value_counts(normalize=True)

        all_categories = sorted(set(baseline_counts.index) | set(current_counts.index))
        if len(all_categories) == 0:
            continue

        baseline_probs = np.array([baseline_counts.get(cat, 0.0) for cat in all_categories])
        current_probs = np.array([current_counts.get(cat, 0.0) for cat in all_categories])

        js_divergence = float(jensenshannon(baseline_probs, current_probs, base=2))
        if np.isnan(js_divergence):
            js_divergence = 0.0

        new_categories = sorted(set(current_counts.index) - set(baseline_counts.index))
        removed_categories = sorted(set(baseline_counts.index) - set(current_counts.index))

        drift_detected = js_divergence > DRIFT_JS_DIVERGENCE_THRESHOLD

        results.append({
            "column": column,
            "drift_detected": bool(drift_detected),
            "js_divergence": round(js_divergence, 4),
            "new_categories": new_categories,
            "removed_categories": removed_categories,
            "explanation": (
                f"Column '{column}' shows notable distribution change "
                f"(JS divergence={round(js_divergence, 4)})."
                if drift_detected else
                f"Column '{column}' shows no significant distribution change."
            ) + (
                f" New categories detected: {new_categories}." if new_categories else ""
            ) + (
                f" Categories no longer present: {removed_categories}." if removed_categories else ""
            ),
        })

    return results

def compare_datasets(baseline_df: pd.DataFrame, current_df: pd.DataFrame) -> dict:
    """
    Run the full drift comparison pipeline: schema comparison, numerical
    drift, and categorical drift. This is the single entry point the API
    should call.
    """
    schema = compare_schemas(baseline_df, current_df)
    numerical_drift = detect_numerical_drift(baseline_df, current_df, schema["common_columns"])
    categorical_drift = detect_categorical_drift(baseline_df, current_df, schema["common_columns"])

    drifted_columns = [r["column"] for r in numerical_drift if r["drift_detected"]] + [
        r["column"] for r in categorical_drift if r["drift_detected"]
    ]

    return {
        "schema_comparison": schema,
        "numerical_drift": numerical_drift,
        "categorical_drift": categorical_drift,
        "summary": {
            "total_columns_compared": len(schema["common_columns"]),
            "columns_with_drift": drifted_columns,
            "drift_detected": len(drifted_columns) > 0,
            "note": (
                "Drift means the distribution changed between the two datasets. "
                "It does not automatically mean the data is bad -- investigate "
                "whether the change reflects a real business shift, a new data "
                "source, or a collection error."
            ),
        },
    }