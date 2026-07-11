from fastapi.testclient import TestClient

from app.main import app


def test_homepage_default_locale_renders_english():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'lang="en"' in html
    assert 'Upload Your File' in html
    assert 'Convert Any File' in html
    assert 'In Seconds' in html
    assert 'window.appLocale' in html
    assert 'window.localeCode = "en"' in html


def test_homepage_lang_query_changes_locale_to_indonesian():
    client = TestClient(app)
    response = client.get("/?lang=id")

    assert response.status_code == 200
    html = response.text

    assert 'lang="id"' in html
    assert 'Unggah File Anda' in html
    assert 'Konversi Semua File' in html
    assert 'Dalam Hitungan Detik' in html
    assert 'window.appLocale' in html
    assert 'window.localeCode = "id"' in html


def test_jpg_to_pdf_landing_page_renders_localized_text_and_frontend_locale():
    client = TestClient(app)

    english_response = client.get("/jpg-to-pdf")
    assert english_response.status_code == 200
    english_html = english_response.text

    assert 'lang="en"' in english_html
    assert 'Upload Your File' in english_html
    assert 'Convert now' in english_html
    assert 'window.appLocale' in english_html
    assert 'window.translate = function' in english_html

    indonesian_response = client.get("/jpg-to-pdf?lang=id")
    assert indonesian_response.status_code == 200
    indonesian_html = indonesian_response.text

    assert 'lang="id"' in indonesian_html
    assert 'Unggah File Anda' in indonesian_html
    assert 'Konversi sekarang' in indonesian_html
    assert 'window.appLocale' in indonesian_html
    assert 'window.localeCode = "id"' in indonesian_html
