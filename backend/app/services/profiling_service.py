import pandas as pd


def calculate_missing_statistics(df: pd.DataFrame) -> dict[str, dict]:
    """
    Calculate missing value count and percentage for every column.

    Returns a dict keyed by column name, e.g.:
    {
        "age": {"missing_count": 3, "missing_percentage": 15.0},
        ...
    }
    """
    total_rows = len(df)
    result: dict[str, dict] = {}

    for column in df.columns:
        missing_count = int(df[column].isna().sum())
        missing_percentage = (
            round((missing_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        )
        result[column] = {
            "missing_count": missing_count,
            "missing_percentage": missing_percentage,
        }

    return result
def calculate_numeric_statistics(df: pd.DataFrame) -> dict[str, dict]:
    """
    Calculate descriptive statistics for numeric columns only.

    Returns a dict keyed by column name, e.g.:
    {
        "age": {"mean": 34.2, "median": 33.0, "std": 10.1, "min": -5.0, "max": 60.0},
        ...
    }
    Non-numeric columns are skipped, EXCEPT columns that are entirely missing:
    an all-null column defaults to pandas 'object' dtype (since there's no
    actual value to infer a numeric type from), which would otherwise make it
    invisible here. We can't know its true intended type from the data alone,
    so we conservatively still report it, with None stats, rather than
    silently dropping a fully-missing column from the profile.
    """
    result: dict[str, dict] = {}
    numeric_columns = list(df.select_dtypes(include="number").columns)
    all_null_columns = [
        column for column in df.columns
        if df[column].isna().all() and column not in numeric_columns
    ]

    for column in numeric_columns + all_null_columns:
        series = df[column].dropna()

        if len(series) == 0:
            result[column] = {
                "mean": None,
                "median": None,
                "std": None,
                "min": None,
                "max": None,
            }
            continue

        result[column] = {
            "mean": round(float(series.mean()), 2),
            "median": round(float(series.median()), 2),
            "std": round(float(series.std()), 2) if len(series) > 1 else 0.0,
            "min": round(float(series.min()), 2),
            "max": round(float(series.max()), 2),
        }

    return result
def calculate_categorical_statistics(df: pd.DataFrame, top_n: int = 3) -> dict[str, dict]:
    """
    Calculate statistics for non-numeric (categorical/text) columns.

    Returns a dict keyed by column name, e.g.:
    {
        "country": {
            "unique_count": 5,
            "unique_percentage": 25.0,
            "top_values": [("USA", 8), ("India", 4), ("Germany", 2)],
        },
        ...
    }
    """
    result: dict[str, dict] = {}
    total_rows = len(df)
    categorical_columns = df.select_dtypes(exclude="number").columns

    for column in categorical_columns:
        series = df[column].dropna()
        unique_count = int(series.nunique())
        unique_percentage = (
            round((unique_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        )
        value_counts = series.value_counts().head(top_n)
        top_values = [(str(k), int(v)) for k, v in value_counts.items()]

        result[column] = {
            "unique_count": unique_count,
            "unique_percentage": unique_percentage,
            "top_values": top_values,
        }

    return result
def profile_dataset(df: pd.DataFrame) -> dict:
    """
    Build a complete profile of the dataset by combining all individual
    profiling functions into one structured result.
    """
    return {
        "num_rows": len(df),
        "num_columns": len(df.columns),
        "column_names": list(df.columns),
        "duplicate_row_count": int(df.duplicated().sum()),
        "missing_statistics": calculate_missing_statistics(df),
        "numeric_statistics": calculate_numeric_statistics(df),
        "categorical_statistics": calculate_categorical_statistics(df),
    }