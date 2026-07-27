from fastapi.testclient import TestClient

from app.main import app


def test_homepage_default_locale_renders_english():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'lang="en"' in html
    assert 'Upload Your File' in html
    assert 'Convert All Files' in html
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


def test_homepage_renders_translated_hero_copy_for_spanish_locale():
    client = TestClient(app)
    response = client.get("/?lang=es")

    assert response.status_code == 200
    html = response.text

    assert 'lang="es"' in html
    assert 'Convierte archivos más rápido con simplicidad premium.' in html
    assert 'hero-cta-primary' not in html
    assert 'Sube tu archivo' in html
    assert 'window.localeCode = "es"' in html


def test_homepage_hero_has_no_extra_ctas_and_visible_drop_zone():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    html = response.text

    assert 'hero-cta-primary' not in html
    assert 'hero-cta-secondary' not in html
    assert 'class="drop-zone"' in html
    assert 'id="dropZone"' in html
    assert 'id="chooseFile"' in html


def test_japanese_homepage_uses_translated_trust_and_support_copy():
    client = TestClient(app)
    response = client.get("/?lang=ja")

    assert response.status_code == 200
    html = response.text

    assert '安全な処理' in html
    assert 'ブラウザベース' in html
    assert '高速変換' in html
    assert '幅広いフォーマット対応' in html
    assert 'ユーザーに信頼されています' in html
    assert '使い方' in html
    assert 'お問い合わせ' in html


def test_navbar_and_hero_subtitle_are_localized_for_spanish_and_french():
    client = TestClient(app)

    spanish_response = client.get("/?lang=es")
    spanish_html = spanish_response.text
    assert 'Herramientas' in spanish_html
    assert 'Soporte' in spanish_html
    assert 'Empezar' in spanish_html
    assert 'que soporta más de 100 formatos.' in spanish_html

    french_response = client.get("/?lang=fr")
    french_html = french_response.text
    assert 'Outils' in french_html
    assert 'Support' in french_html
    assert 'Commencer' in french_html
    assert 'qui prend en charge plus de 100 formats.' in french_html


def test_indonesian_hero_subtitle_uses_full_translation_without_english_tail():
    client = TestClient(app)
    response = client.get("/?lang=id")

    assert response.status_code == 200
    html = response.text

    assert 'yang mendukung lebih dari 100 format.' in html
    assert 'that supports 100+ formats.' not in html


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
