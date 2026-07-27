from pathlib import Path

from fastapi.testclient import TestClient

from app.core.settings import settings
import app.main as main


def test_download_route_serves_attachment_headers(tmp_path, monkeypatch):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    conversion_id = "conv-123"
    sample_file = output_dir / conversion_id / "converted.mp3"
    sample_file.parent.mkdir(parents=True, exist_ok=True)
    sample_file.write_bytes(b"ID3\x03\x00")

    monkeypatch.setattr(main, "OUTPUT_DIR", output_dir)
    monkeypatch.setattr(main.settings, "OUTPUT_DIR", output_dir, raising=False)
    monkeypatch.setattr(settings, "OUTPUT_DIR", output_dir, raising=False)

    client = TestClient(main.app)
    response = client.get(f"/download/{conversion_id}/converted.mp3")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"].lower()
    assert 'filename="converted.mp3"' in response.headers["content-disposition"]
    assert response.headers["content-type"].startswith("audio/mpeg")
