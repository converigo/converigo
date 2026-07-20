from pathlib import Path

from fastapi.testclient import TestClient

import app.main as main


def test_download_route_serves_attachment_headers(tmp_path, monkeypatch):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    sample_file = output_dir / "converted.mp3"
    sample_file.write_bytes(b"ID3\x03\x00")

    monkeypatch.setattr(main, "OUTPUT_DIR", output_dir)

    client = TestClient(main.app)
    response = client.get("/download/converted.mp3")

    assert response.status_code == 200
    assert "attachment" in response.headers["content-disposition"].lower()
    assert 'filename="converted.mp3"' in response.headers["content-disposition"]
    assert response.headers["content-type"].startswith("audio/mpeg")
