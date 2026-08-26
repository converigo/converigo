from pathlib import Path
import json

from fastapi.testclient import TestClient

from app.main import app


def _two_sample_files():
    sample_path1 = Path(__file__).parent.parent / "test_files" / "sample.jpg"
    sample_path2 = Path(__file__).parent.parent / "test_files" / "sample.png"
    return sample_path1, sample_path2


def test_targets_malformed_json_returns_400():
    client = TestClient(app)
    a, b = _two_sample_files()
    with a.open("rb") as f1, b.open("rb") as f2:
        response = client.post(
            "/convert",
            files=[
                ("file", (a.name, f1, "image/jpeg")),
                ("file", (b.name, f2, "image/png")),
            ],
            data={"targets": "not-a-json"},
        )

    assert response.status_code == 400
    assert response.json().get("detail") == "targets must be a valid JSON array"


def test_targets_length_mismatch_returns_400():
    client = TestClient(app)
    a, b = _two_sample_files()
    with a.open("rb") as f1, b.open("rb") as f2:
        response = client.post(
            "/convert",
            files=[
                ("file", (a.name, f1, "image/jpeg")),
                ("file", (b.name, f2, "image/png")),
            ],
            data={"targets": json.dumps(["webp"])},
        )

    assert response.status_code == 400
    assert response.json().get("detail") == "targets length must match number of files"


def test_no_targets_or_target_format_returns_400():
    client = TestClient(app)
    a, b = _two_sample_files()
    with a.open("rb") as f1, b.open("rb") as f2:
        response = client.post(
            "/convert",
            files=[
                ("file", (a.name, f1, "image/jpeg")),
                ("file", (b.name, f2, "image/png")),
            ],
        )

    assert response.status_code == 400
    assert response.json().get("detail") == "no target format specified"
