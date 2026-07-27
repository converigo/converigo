from fastapi.testclient import TestClient

from app.main import app


def test_learning_index_lists_articles() -> None:
    client = TestClient(app)
    response = client.get("/learning")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_learning_article_returns_existing_article() -> None:
    client = TestClient(app)
    response = client.get("/learning/getting-started")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_learning_article_returns_png_hub() -> None:
    client = TestClient(app)
    response = client.get("/learning/png")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_learning_article_returns_png_supporting_article() -> None:
    client = TestClient(app)
    response = client.get("/learning/what-is-png")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_learning_article_returns_404_for_missing_article() -> None:
    client = TestClient(app)
    response = client.get("/learning/does-not-exist")

    assert response.status_code == 404
