"""Tests for the /certification redirect route."""

from fastapi.testclient import TestClient

from app.main import app


class TestCertificationRedirect:
    """Verify /certification returns a 301 redirect to /."""

    def test_certification_redirects_to_home(self):
        client = TestClient(app)
        response = client.get("/certification", follow_redirects=False)

        # Must NOT be 500 (NameError from missing RedirectResponse import)
        assert response.status_code != 500
        assert response.status_code == 301
        assert response.headers["location"] == "/"

    def test_certification_follow_redirect_ends_at_home(self):
        client = TestClient(app)
        response = client.get("/certification", follow_redirects=True)

        assert response.status_code == 200
        assert "Converigo" in response.text