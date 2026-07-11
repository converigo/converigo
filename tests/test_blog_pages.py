from fastapi.testclient import TestClient

from app.main import app


def test_blog_index_and_articles_are_available():
    client = TestClient(app)

    for path in ["/blog", "/blog/how-to-convert-mp4-to-mp3", "/blog/jpg-to-pdf-guide", "/blog/png-to-jpg-guide"]:
        response = client.get(path)
        assert response.status_code == 200, f"Expected {path} to be available"
        assert "text/html" in response.headers.get("content-type", "")
