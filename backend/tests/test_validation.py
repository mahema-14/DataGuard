import pandas as pd
import pytest

from backend.app.services.profiling_service import (
    calculate_missing_statistics,
    calculate_categorical_statistics,
    profile_dataset,
)
from backend.app.services.validation_service import (
    check_missing_values,
    check_constant_columns,
    check_duplicate_rows,
    check_high_cardinality,
    check_rare_categories,
    detect_outliers,
    check_invalid_values,
    run_all_checks,
)


@pytest.fixture
def sample_df():
    return pd.read_csv("data/sample/dataguard_sample_v1.csv")


def test_check_missing_values_flags_age_as_warning(sample_df):
    stats = calculate_missing_statistics(sample_df)
    issues = check_missing_values(stats)
    assert len(issues) == 1
    assert issues[0]["column"] == "age"
    assert issues[0]["severity"] == "warning"


def test_check_constant_columns_flags_plan_type(sample_df):
    stats = calculate_categorical_statistics(sample_df)
    issues = check_constant_columns(stats, len(sample_df))
    assert len(issues) == 1
    assert issues[0]["column"] == "plan_type"


def test_check_duplicate_rows_ignores_id_differing_rows(sample_df):
    # Verified earlier: pandas finds 0 full-row duplicates here because
    # customer_id differs even when every other column is identical.
    profile = profile_dataset(sample_df)
    issues = check_duplicate_rows(profile["duplicate_row_count"], profile["num_rows"])
    assert issues == []


def test_check_duplicate_rows_triggers_on_synthetic_case():
    issues = check_duplicate_rows(duplicate_row_count=3, num_rows=20)
    assert len(issues) == 1
    assert issues[0]["measured_value"] == 15.0


def test_check_high_cardinality_flags_customer_id(sample_df):
    stats = calculate_categorical_statistics(sample_df)
    issues = check_high_cardinality(stats)
    columns_flagged = [i["column"] for i in issues]
    assert "customer_id" in columns_flagged
    assert "signup_date" not in columns_flagged  # 90%, below 95% threshold


def test_detect_outliers_flags_purchase_amount_only(sample_df):
    issues = detect_outliers(sample_df, ["age", "purchase_amount"])
    columns_flagged = [i["column"] for i in issues]
    assert "purchase_amount" in columns_flagged
    assert "age" not in columns_flagged


def test_check_invalid_values_flags_negative_age(sample_df):
    issues = check_invalid_values(sample_df, {"age": {"min": 0}})
    assert len(issues) == 1
    assert issues[0]["measured_value"] == 1
    assert issues[0]["severity"] == "critical"


def test_run_all_checks_returns_four_issues_at_real_thresholds(sample_df):
    profile = profile_dataset(sample_df)
    issues = run_all_checks(sample_df, profile)
    assert len(issues) == 4
    issue_types = {i["issue_type"] for i in issues}
    assert issue_types == {
        "high_missing_values",
        "constant_column",
        "high_cardinality",
        "numeric_outliers",
    }