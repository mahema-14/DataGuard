import io

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_health_check_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_upload_rejects_non_csv_file():
    fake_file = io.BytesIO(b"not a real csv")
    response = client.post(
        "/datasets/upload",
        files={"file": ("data.txt", fake_file, "text/plain")},
    )
    assert response.status_code == 400


def test_upload_rejects_empty_file():
    empty_file = io.BytesIO(b"")
    response = client.post(
        "/datasets/upload",
        files={"file": ("empty.csv", empty_file, "text/csv")},
    )
    assert response.status_code == 400


def test_upload_accepts_valid_csv_and_returns_dataset_id():
    with open("data/sample/dataguard_sample_v1.csv", "rb") as f:
        response = client.post(
            "/datasets/upload",
            files={"file": ("dataguard_sample_v1.csv", f, "text/csv")},
        )
    assert response.status_code == 200
    body = response.json()
    assert "dataset_id" in body
    assert body["num_rows"] == 20
    assert body["num_columns"] == 7


def test_quality_report_returns_404_for_unknown_dataset():
    response = client.get("/datasets/nonexistent-id/quality-report")
    assert response.status_code == 404


def test_full_upload_then_quality_report_flow():
    with open("data/sample/dataguard_sample_v1.csv", "rb") as f:
        upload_response = client.post(
            "/datasets/upload",
            files={"file": ("dataguard_sample_v1.csv", f, "text/csv")},
        )
    dataset_id = upload_response.json()["dataset_id"]

    report_response = client.get(f"/datasets/{dataset_id}/quality-report")
    assert report_response.status_code == 200
    body = report_response.json()
    assert body["quality_score"]["overall_score"] == 95.89
    assert body["num_issues"] == 4