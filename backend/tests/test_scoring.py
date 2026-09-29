import pandas as pd
import pytest

from backend.app.services.profiling_service import profile_dataset
from backend.app.services.validation_service import run_all_checks
from backend.app.services.scoring_service import (
    calculate_completeness_score,
    calculate_uniqueness_score,
    calculate_outlier_health_score,
    calculate_validity_score,
    calculate_consistency_score,
    calculate_overall_score,
    calculate_quality_score,
)


@pytest.fixture
def sample_df():
    return pd.read_csv("data/sample/dataguard_sample_v1.csv")


def test_calculate_quality_score_matches_hand_verified_result(sample_df):
    profile = profile_dataset(sample_df)
    issues = run_all_checks(sample_df, profile)
    result = calculate_quality_score(sample_df, profile, issues)

    assert result["overall_score"] == 95.89
    assert result["sub_scores"]["completeness"] == 97.86
    assert result["sub_scores"]["validity"] == 100.0
    assert result["sub_scores"]["uniqueness"] == 100.0
    assert result["sub_scores"]["consistency"] == 71.43
    assert result["sub_scores"]["outlier_health"] == 95.0


def test_overall_score_weights_sum_to_full_contribution():
    sub_scores = {
        "completeness": 100.0,
        "validity": 100.0,
        "uniqueness": 100.0,
        "consistency": 100.0,
        "outlier_health": 100.0,
    }
    result = calculate_overall_score(sub_scores)
    # All sub-scores perfect -> overall must also be a perfect 100
    assert result["overall_score"] == 100.0


def test_completeness_score_handles_empty_dataframe():
    assert calculate_completeness_score({}) == 100.0


def test_scores_are_never_negative_on_severely_corrupted_dataset():
    # A dataset with 100% missing values, 100% duplicates, and severe outliers.
    corrupted_df = pd.DataFrame({
        "value": [None] * 10,
    })
    profile = profile_dataset(corrupted_df)
    issues = run_all_checks(corrupted_df, profile)
    result = calculate_quality_score(corrupted_df, profile, issues)

    for sub_score in result["sub_scores"].values():
        assert 0.0 <= sub_score <= 100.0
    assert 0.0 <= result["overall_score"] <= 100.0


def test_uniqueness_score_zero_rows_returns_100():
    assert calculate_uniqueness_score(duplicate_row_count=0, num_rows=0) == 100.0
    