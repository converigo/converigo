import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_mp4_to_mp3_legacy_page_is_retired():
    client = TestClient(app)

    response = client.get("/mp4-to-mp3")

    assert response.status_code == 410


def test_mp4_to_mp3_canonical_page_renders_with_seo_and_faq():
    client = TestClient(app)

    response = client.get("/tools/mp4-to-mp3")

    assert response.status_code == 200
    assert "Convert MP4 to MP3 Online Free | Converigo" in response.text
    assert "Convert MP4 videos to MP3 audio online for free. Extract audio from video, preserve quality, and download your MP3 instantly in the browser." in response.text
    assert "application/ld+json" in response.text
    assert "@type\": \"SoftwareApplication\"" in response.text
    assert "@type\": \"BreadcrumbList\"" in response.text
    assert "href=\"#converter\"" in response.text
    assert "href=\"#how-to-use\"" in response.text
    assert "href=\"#supported-formats\"" in response.text
    assert "href=\"#faq\"" in response.text
    assert "href=\"#related-tools\"" in response.text
    assert "MP4 input, MP3 output" in response.text
    assert "Download your converted MP3" in response.text
    assert "How to convert MP4 to MP3" in response.text
    assert "/tools/" in response.text


def test_mp4_to_mp3_conversion_endpoint_still_accepts_uploads():
    client = TestClient(app)
    sample_path = Path(__file__).parent / "sample.mp4"

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "video/mp4")},
            data={"target_format": "mp3"},
        )

    assert response.status_code == 201
    assert response.json()["status"] == "success"


# Internal implementation detail that must never ride the public 422 message
# channel (the same marker family tests/test_phase25_d4_guard_no_disclosure.py
# sweeps for).
_INTERNAL_MARKERS = (
    "MP4ToMP3Plugin",
    "Plugin",
    "RuntimeError",
    "ConversionError",
    "UnsupportedConversionError",
    "Traceback",
    "ffmpeg",
    "ffprobe",
    "app.plugins",
    "conversion_service",
    "site-packages",
    ".venv",
    "/app/",
    "uploads\\",
    "uploads/",
    "temp\\",
    ".py",
)


def test_mp4_to_mp3_returns_clear_error_when_input_has_no_audio(tmp_path):
    """An MP4 with no audio track is an unsupported INPUT, not a server fault.

    Locked here as the sanctioned 422 UNSUPPORTED_CONVERSION contract. It used to
    be a 500 whose detail echoed the plugin's raw RuntimeError text, which D4 (F1)
    removed: that echo was the only reason the guidance reached a client, and the
    batch shape of it leaked "error_code": "CONVERSIONERROR" - a Python class
    name. The wording is preserved, but now through the typed channel, so a 500
    stays reserved for failures the user cannot fix by re-uploading a file.
    """
    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        pytest.skip("ffmpeg not available")

    sample_path = tmp_path / "video-only.mp4"
    subprocess.run(
        [
            ffmpeg,
            "-f",
            "lavfi",
            "-i",
            "color=c=black:s=320x240:d=1",
            "-frames:v",
            "1",
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            str(sample_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    client = TestClient(app)

    with sample_path.open("rb") as sample_file:
        response = client.post(
            "/convert",
            files={"file": (sample_path.name, sample_file, "video/mp4")},
            data={"target_format": "mp3"},
        )

    assert response.status_code == 422

    body = response.json()
    assert body["success"] is False
    assert body["code"] == "UNSUPPORTED_CONVERSION"
    # The 500-era shape was {"detail": ...}; the honest channel is the flat
    # {success, code, message} contract.
    assert "detail" not in body

    # The user-facing guidance survived the migration and is still actionable.
    assert "does not contain an audio stream" in body["message"]
    assert "upload a video file that includes audio" in body["message"]

    # ...without dragging any internal detail along with it.
    leaked = [m for m in _INTERNAL_MARKERS if m.lower() in response.text.lower()]
    assert leaked == []

    # Correlation with the server-side log record is still available.
    assert body["request_id"]
    assert body.get("conversion_id")
    assert response.headers["X-Request-ID"] == body["request_id"]

