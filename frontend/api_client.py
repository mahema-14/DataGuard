import os
import requests

API_BASE_URL = os.environ.get("API_BASE_URL", "http://127.0.0.1:8000")


def check_health() -> bool:
    """Return True if the backend is reachable and healthy."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def upload_dataset(file) -> dict:
    """Upload a CSV file to the backend. Raises on failure."""
    files = {"file": (file.name, file.getvalue(), "text/csv")}
    response = requests.post(f"{API_BASE_URL}/datasets/upload", files=files)
    response.raise_for_status()
    return response.json()


def get_dataset_profile(dataset_id: str) -> dict:
    """Fetch the profile for a dataset."""
    response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/profile")
    response.raise_for_status()
    return response.json()


def get_quality_report(dataset_id: str) -> dict:
    """Fetch the quality report (issues + score) for a dataset."""
    response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/quality-report")
    response.raise_for_status()
    return response.json()


def compare_drift(baseline_dataset_id: str, current_dataset_id: str) -> dict:
    """Run a drift comparison between two datasets."""
    response = requests.post(
        f"{API_BASE_URL}/drift/compare",
        params={
            "baseline_dataset_id": baseline_dataset_id,
            "current_dataset_id": current_dataset_id,
        },
    )
    response.raise_for_status()
    return response.json()
def get_column_values(dataset_id: str, column_name: str) -> dict:
    """Fetch raw values for a single numeric column, for charting."""
    response = requests.get(f"{API_BASE_URL}/datasets/{dataset_id}/column/{column_name}/values")
    response.raise_for_status()
    return response.json()