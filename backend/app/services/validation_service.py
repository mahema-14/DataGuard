import pandas as pd
from backend.app.core.thresholds import HIGH_MISSING_CRITICAL_PCT, HIGH_MISSING_WARNING_PCT
from backend.app.core.thresholds import DUPLICATE_WARNING_PCT
from backend.app.core.thresholds import HIGH_CARDINALITY_UNIQUE_PCT
from backend.app.core.thresholds import RARE_CATEGORY_PCT
from backend.app.core.thresholds import OUTLIER_STD_THRESHOLD

def build_quality_issue(
    issue_type: str,
    severity: str,
    explanation: str,
    recommendation: str,
    column: str | None = None,
    measured_value: float | None = None,
    threshold: float | None = None,
) -> dict:
    """
    Build a single structured quality issue.
    Every check in this module should produce issues using this helper,
    so the shape of an issue stays consistent across all check types.
    """
    return {
        "issue_type": issue_type,
        "column": column,
        "severity": severity,
        "measured_value": measured_value,
        "threshold": threshold,
        "explanation": explanation,
        "recommendation": recommendation,
    }


def check_missing_values(missing_statistics: dict) -> list[dict]:
    """
    Flag columns with a high percentage of missing values.
    Takes the output of calculate_missing_statistics() as input, so this
    function doesn't need the raw DataFrame at all.
    """
    issues: list[dict] = []

    for column, stats in missing_statistics.items():
        pct = stats["missing_percentage"]

        if pct >= HIGH_MISSING_CRITICAL_PCT:
            issues.append(build_quality_issue(
                issue_type="high_missing_values",
                severity="critical",
                column=column,
                measured_value=pct,
                threshold=HIGH_MISSING_CRITICAL_PCT,
                explanation=(
                    f"Column '{column}' has {pct}% missing values. "
                    "This severely limits how useful this column can be "
                    "for analysis or model training."
                ),
                recommendation=(
                    "Consider removing this column, or investigate whether "
                    "the missingness follows a pattern (e.g. a specific "
                    "data source or time period) before deciding how to handle it."
                ),
            ))
        elif pct >= HIGH_MISSING_WARNING_PCT:
            issues.append(build_quality_issue(
                issue_type="high_missing_values",
                severity="warning",
                column=column,
                measured_value=pct,
                threshold=HIGH_MISSING_WARNING_PCT,
                explanation=(
                    f"Column '{column}' has {pct}% missing values. "
                    "This may reduce model reliability."
                ),
                recommendation=(
                    "Consider imputing values using a statistically justified "
                    "method (e.g. median for skewed numeric data), removing "
                    "the column, or investigating why values are missing."
                ),
            ))

    return issues


def check_constant_columns(categorical_statistics: dict, num_rows: int) -> list[dict]:
    """
    Flag columns that contain only a single distinct value.
    A constant column provides zero variance, so it carries no
    information for analysis or model training.
    """
    issues: list[dict] = []

    for column, stats in categorical_statistics.items():
        if stats["unique_count"] == 1 and num_rows > 0:
            constant_value = stats["top_values"][0][0]
            issues.append(build_quality_issue(
                issue_type="constant_column",
                severity="warning",
                column=column,
                measured_value=1,
                threshold=1,
                explanation=(
                    f"Column '{column}' contains only one distinct value "
                    f"('{constant_value}') across all {num_rows} rows."
                ),
                recommendation=(
                    "This column provides no variation in the current dataset "
                    "and may be removed from a model, since it cannot help "
                    "distinguish between records."
                ),
            ))

    return issues


def check_duplicate_rows(duplicate_row_count: int, num_rows: int) -> list[dict]:
    """
    Flag when duplicate rows make up a meaningful portion of the dataset.
    Takes the already-computed duplicate count from profile_dataset(),
    so this function stays a simple, testable calculation.
    """
    if num_rows == 0 or duplicate_row_count == 0:
        return []

    pct = round((duplicate_row_count / num_rows) * 100, 2)

    if pct < DUPLICATE_WARNING_PCT:
        return []

    return [build_quality_issue(
        issue_type="duplicate_rows",
        severity="warning",
        column=None,
        measured_value=pct,
        threshold=DUPLICATE_WARNING_PCT,
        explanation=(
            f"{duplicate_row_count} duplicate rows detected "
            f"({pct}% of the dataset)."
        ),
        recommendation=(
            "Check whether duplicates represent repeated events (e.g. "
            "legitimate re-purchases) or accidental duplication (e.g. a "
            "failed upload retried) before deciding whether to remove them."
        ),
    )]


def check_high_cardinality(categorical_statistics: dict) -> list[dict]:
    """
    Flag categorical columns where nearly every value is unique.
    These columns behave like identifiers rather than useful features
    for grouping, filtering, or model training.
    """
    issues: list[dict] = []

    for column, stats in categorical_statistics.items():
        pct = stats["unique_percentage"]

        if pct >= HIGH_CARDINALITY_UNIQUE_PCT:
            issues.append(build_quality_issue(
                issue_type="high_cardinality",
                severity="informational",
                column=column,
                measured_value=pct,
                threshold=HIGH_CARDINALITY_UNIQUE_PCT,
                explanation=(
                    f"Column '{column}' has {pct}% unique values, suggesting "
                    "it behaves like an identifier rather than a categorical feature."
                ),
                recommendation=(
                    "If this is an ID column, exclude it from model features. "
                    "If it's meant to be a meaningful category, investigate "
                    "why almost every value is unique."
                ),
            ))

    return issues
def check_rare_categories(
    df, categorical_columns: list[str], rare_threshold_pct: float = RARE_CATEGORY_PCT
) -> list[dict]:
    """
    Flag categorical values that appear in a very small fraction of rows.
    Rare categories are often too sparse for a model to learn a reliable
    pattern from, and may indicate typos or one-off data entry errors.
    """
    issues: list[dict] = []
    total_rows = len(df)

    if total_rows == 0:
        return issues

    for column in categorical_columns:
        value_counts = df[column].dropna().value_counts()

        if len(value_counts) <= 1:
            continue

        for value, count in value_counts.items():
            pct = round((count / total_rows) * 100, 2)
            if pct <= rare_threshold_pct:
                issues.append(build_quality_issue(
                    issue_type="rare_category",
                    severity="informational",
                    column=column,
                    measured_value=pct,
                    threshold=rare_threshold_pct,
                    explanation=(
                        f"In column '{column}', the value '{value}' appears in only "
                        f"{count} row(s) ({pct}% of the dataset)."
                    ),
                    recommendation=(
                        "Rare categories may be legitimate (e.g. a new customer "
                        "segment), or could indicate a typo or data entry error. "
                        "Consider grouping rare categories into an 'Other' bucket "
                        "if they are too sparse for reliable model learning."
                    ),
                ))

    return issues
def detect_outliers(df, numeric_columns: list[str]) -> list[dict]:
    """
    Flag numeric columns containing values far from the mean, using the
    standard deviation (z-score) method. A value is an outlier if it is
    more than OUTLIER_STD_THRESHOLD standard deviations from the mean.

    Note: outliers are not automatically "wrong" -- they may be legitimate
    extreme values. This check surfaces them for human judgement.
    """
    issues: list[dict] = []

    for column in numeric_columns:
        series = df[column].dropna()

        # Need at least a few points for mean/std to be meaningful,
        # and std must be non-zero (a constant numeric column has no outliers).
        if len(series) < 3:
            continue
        std = series.std()
        if std == 0 or pd.isna(std):
            continue

        mean = series.mean()
        z_scores = (series - mean).abs() / std
        outlier_mask = z_scores > OUTLIER_STD_THRESHOLD
        outlier_count = int(outlier_mask.sum())

        if outlier_count == 0:
            continue

        outlier_values = series[outlier_mask].tolist()
        pct = round((outlier_count / len(series)) * 100, 2)

        issues.append(build_quality_issue(
            issue_type="numeric_outliers",
            severity="informational",
            column=column,
            measured_value=outlier_count,
            threshold=OUTLIER_STD_THRESHOLD,
            explanation=(
                f"Column '{column}' has {outlier_count} value(s) more than "
                f"{OUTLIER_STD_THRESHOLD} standard deviations from the mean "
                f"(e.g. {outlier_values[:3]}), out of {len(series)} non-missing values "
                f"({pct}%)."
            ),
            recommendation=(
                "Outliers may be legitimate extreme values (e.g. a genuine "
                "large purchase) or data entry errors. Investigate the "
                "specific rows before deciding whether to cap, remove, or keep them."
            ),
        ))

    return issues
def check_invalid_values(
    df,
    rules: dict[str, dict],
) -> list[dict]:
    """
    Flag values that violate user-defined validity rules.

    `rules` maps column name to a dict of constraints, e.g.:
        {"age": {"min": 0, "max": 120}}
    Only constraints that are actually provided are checked -- a column
    can have just a min, just a max, or both.
    """
    issues: list[dict] = []

    for column, constraints in rules.items():
        if column not in df.columns:
            continue

        series = df[column].dropna()
        min_value = constraints.get("min")
        max_value = constraints.get("max")

        violations = pd.Series(dtype=bool)
        if min_value is not None:
            violations = series < min_value
        if max_value is not None:
            max_violations = series > max_value
            violations = violations | max_violations if len(violations) else max_violations

        violation_count = int(violations.sum()) if len(violations) else 0
        if violation_count == 0:
            continue

        example_values = series[violations].tolist()[:3]
        rule_description = ", ".join(
            f"{k}={v}" for k, v in constraints.items() if v is not None
        )

        issues.append(build_quality_issue(
            issue_type="invalid_value",
            severity="critical",
            column=column,
            measured_value=violation_count,
            threshold=None,
            explanation=(
                f"Column '{column}' has {violation_count} value(s) violating "
                f"the configured rule ({rule_description}), e.g. {example_values}."
            ),
            recommendation=(
                "These values fall outside the range considered valid for "
                "this column. Investigate whether they represent data entry "
                "errors, sensor faults, or a misunderstanding of the expected range."
            ),
        ))

    return issues
def run_all_checks(df, profile: dict, invalid_value_rules: dict[str, dict] | None = None) -> list[dict]:
    """
    Run every quality check against a dataset and its precomputed profile,
    and return a single combined list of issues.

    `profile` is expected to be the output of profile_dataset().
    `invalid_value_rules` is optional -- only columns with explicit rules
    are checked for invalid values.
    """
    numeric_columns = list(profile["numeric_statistics"].keys())
    categorical_columns = list(profile["categorical_statistics"].keys())

    issues: list[dict] = []
    issues += check_missing_values(profile["missing_statistics"])
    issues += check_constant_columns(profile["categorical_statistics"], profile["num_rows"])
    issues += check_duplicate_rows(profile["duplicate_row_count"], profile["num_rows"])
    issues += check_high_cardinality(profile["categorical_statistics"])
    issues += check_rare_categories(df, categorical_columns)
    issues += detect_outliers(df, numeric_columns)

    if invalid_value_rules:
        issues += check_invalid_values(df, invalid_value_rules)

    return issues