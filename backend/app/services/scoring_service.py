from backend.app.core.thresholds import SCORE_WEIGHTS

def calculate_completeness_score(missing_statistics: dict) -> float:
    """
    Completeness score: how complete (non-missing) the dataset is overall.
    Computed as 100 minus the average missing percentage across all columns.
    A dataset with no missing values anywhere scores 100.
    """
    if not missing_statistics:
        return 100.0

    percentages = [stats["missing_percentage"] for stats in missing_statistics.values()]
    average_missing_pct = sum(percentages) / len(percentages)
    score = 100.0 - average_missing_pct
    return round(max(0.0, min(100.0, score)), 2)
def calculate_uniqueness_score(duplicate_row_count: int, num_rows: int) -> float:
    """
    Uniqueness score: how free of duplicate rows the dataset is.
    A dataset with zero duplicate rows scores 100.
    """
    if num_rows == 0:
        return 100.0

    duplicate_pct = (duplicate_row_count / num_rows) * 100
    score = 100.0 - duplicate_pct
    return round(max(0.0, min(100.0, score)), 2)

def calculate_outlier_health_score(outlier_issues: list[dict], num_rows: int) -> float:
    """
    Outlier health score: how free of statistical outliers the dataset is.
    Uses the issues already produced by detect_outliers(). Penalizes based
    on total outlier value count relative to dataset size, since a few
    outliers in a large dataset matter less than the same count in a small one.
    """
    if num_rows == 0:
        return 100.0

    total_outliers = sum(issue["measured_value"] for issue in outlier_issues)
    outlier_pct = (total_outliers / num_rows) * 100
    score = 100.0 - outlier_pct
    return round(max(0.0, min(100.0, score)), 2)

def calculate_validity_score(invalid_value_issues: list[dict], num_rows: int) -> float:
    """
    Validity score: how free of rule-violating (invalid) values the dataset is.
    Based only on issues from check_invalid_values(). If no rules were
    configured, there is nothing to violate, so the score is 100.
    """
    if num_rows == 0:
        return 100.0

    total_invalid = sum(issue["measured_value"] for issue in invalid_value_issues)
    invalid_pct = (total_invalid / num_rows) * 100
    score = 100.0 - invalid_pct
    return round(max(0.0, min(100.0, score)), 2)


def calculate_consistency_score(structural_issues: list[dict], num_columns: int) -> float:
    """
    Consistency score: how structurally sound the dataset's columns are.
    Based on constant_column and high_cardinality issues, measured as a
    fraction of *columns* affected (not rows), since these are column-level
    structural problems rather than value-level ones.
    """
    if num_columns == 0:
        return 100.0

    affected_columns = len(structural_issues)
    affected_pct = (affected_columns / num_columns) * 100
    score = 100.0 - affected_pct
    return round(max(0.0, min(100.0, score)), 2)

def calculate_overall_score(sub_scores: dict[str, float]) -> dict:
    """
    Combine sub-scores into a single weighted overall quality score.

    `sub_scores` must contain keys matching SCORE_WEIGHTS:
    completeness, validity, uniqueness, consistency, outlier_health.

    Returns the overall score along with each sub-score's weighted
    contribution, so the frontend can show *why* the score is what it is.
    """
    weighted_contributions = {
        name: round(sub_scores[name] * weight, 2)
        for name, weight in SCORE_WEIGHTS.items()
    }
    overall = round(sum(weighted_contributions.values()), 2)

    return {
        "overall_score": overall,
        "sub_scores": sub_scores,
        "weighted_contributions": weighted_contributions,
        "weights_used": SCORE_WEIGHTS,
        "note": (
            "This score is a practical heuristic based on configurable rules, "
            "not a universal or scientific measure of data quality."
        ),
    }


def calculate_quality_score(df, profile: dict, issues: list[dict]) -> dict:
    """
    Compute the full quality score breakdown from a profile and its
    detected issues. This is the single entry point the API should call.
    """
    outlier_issues = [i for i in issues if i["issue_type"] == "numeric_outliers"]
    invalid_issues = [i for i in issues if i["issue_type"] == "invalid_value"]
    structural_issues = [
        i for i in issues if i["issue_type"] in ("constant_column", "high_cardinality")
    ]

    sub_scores = {
        "completeness": calculate_completeness_score(profile["missing_statistics"]),
        "validity": calculate_validity_score(invalid_issues, profile["num_rows"]),
        "uniqueness": calculate_uniqueness_score(profile["duplicate_row_count"], profile["num_rows"]),
        "consistency": calculate_consistency_score(structural_issues, profile["num_columns"]),
        "outlier_health": calculate_outlier_health_score(outlier_issues, profile["num_rows"]),
    }

    return calculate_overall_score(sub_scores)