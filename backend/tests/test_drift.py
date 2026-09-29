import pandas as pd
import pytest

from backend.app.services.drift_service import (
    compare_schemas,
    detect_numerical_drift,
    detect_categorical_drift,
    compare_datasets,
)


@pytest.fixture
def baseline_df():
    return pd.read_csv("data/sample/dataguard_sample_v1.csv")


@pytest.fixture
def current_df():
    return pd.read_csv("data/sample/dataguard_sample_v2.csv")


def test_compare_schemas_detects_added_and_removed_columns(baseline_df, current_df):
    result = compare_schemas(baseline_df, current_df)
    assert result["added_columns"] == ["referral_source"]
    assert result["removed_columns"] == ["plan_type"]
    assert result["row_count_change"] == 0


def test_numerical_drift_flags_purchase_amount_not_age(baseline_df, current_df):
    schema = compare_schemas(baseline_df, current_df)
    results = detect_numerical_drift(baseline_df, current_df, schema["common_columns"])
    by_column = {r["column"]: r for r in results}

    assert by_column["purchase_amount"]["drift_detected"] is True
    assert by_column["age"]["drift_detected"] is False


def test_categorical_drift_excludes_high_cardinality_columns(baseline_df, current_df):
    schema = compare_schemas(baseline_df, current_df)
    results = detect_categorical_drift(baseline_df, current_df, schema["common_columns"])
    columns_checked = [r["column"] for r in results]

    # customer_id, email, signup_date are near-100% unique and must be excluded
    assert "customer_id" not in columns_checked
    assert "email" not in columns_checked
    assert "signup_date" not in columns_checked
    assert "country" in columns_checked


def test_categorical_drift_detects_new_and_removed_categories(baseline_df, current_df):
    schema = compare_schemas(baseline_df, current_df)
    results = detect_categorical_drift(baseline_df, current_df, schema["common_columns"])
    country_result = next(r for r in results if r["column"] == "country")

    assert "Japan" in country_result["new_categories"]
    assert "Nepal" in country_result["removed_categories"]


def test_compare_datasets_full_pipeline_summary(baseline_df, current_df):
    result = compare_datasets(baseline_df, current_df)
    assert result["summary"]["drift_detected"] is True
    assert set(result["summary"]["columns_with_drift"]) == {"purchase_amount", "country"}


def test_numerical_drift_handles_identical_datasets(baseline_df):
    # Comparing a dataset against itself should show no drift anywhere.
    schema = compare_schemas(baseline_df, baseline_df)
    results = detect_numerical_drift(baseline_df, baseline_df, schema["common_columns"])
    assert all(r["drift_detected"] is False for r in results)