import pandas as pd
import pytest

from backend.app.services.profiling_service import (
    calculate_missing_statistics,
    calculate_numeric_statistics,
    calculate_categorical_statistics,
    profile_dataset,
)


@pytest.fixture
def sample_df():
    """Load the known sample dataset used throughout manual testing."""
    return pd.read_csv("data/sample/dataguard_sample_v1.csv")


def test_missing_statistics_detects_known_missing_column(sample_df):
    result = calculate_missing_statistics(sample_df)
    assert result["age"]["missing_count"] == 3
    assert result["age"]["missing_percentage"] == 15.0
    assert result["customer_id"]["missing_count"] == 0


def test_numeric_statistics_detects_outlier_in_max(sample_df):
    result = calculate_numeric_statistics(sample_df)
    assert result["purchase_amount"]["max"] == 999999.0
    assert result["age"]["min"] == -5.0


def test_categorical_statistics_detects_constant_and_identifier_columns(sample_df):
    result = calculate_categorical_statistics(sample_df)
    assert result["plan_type"]["unique_count"] == 1
    assert result["customer_id"]["unique_count"] == 20
    assert result["customer_id"]["unique_percentage"] == 100.0


def test_profile_dataset_returns_expected_shape(sample_df):
    profile = profile_dataset(sample_df)
    assert profile["num_rows"] == 20
    assert profile["num_columns"] == 7
    assert "age" in profile["column_names"]
    assert profile["duplicate_row_count"] == 0  # verified: customer_id differs, so no full-row dupes


def test_missing_statistics_handles_empty_dataframe():
    empty_df = pd.DataFrame()
    result = calculate_missing_statistics(empty_df)
    assert result == {}


def test_numeric_statistics_handles_all_missing_column():
    df = pd.DataFrame({"value": [None, None, None]})
    result = calculate_numeric_statistics(df)
    assert result["value"]["mean"] is None
    assert result["value"]["min"] is None