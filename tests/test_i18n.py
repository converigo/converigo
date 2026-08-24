from fastapi.testclient import TestClient

from app.main import app
import re, json


def extract_app_locale(page_html: str) -> dict:
    """Extract the JS `window.appLocale` object from rendered HTML and return parsed JSON.
    Returns empty dict on failure. Works by finding the first '{' after the assignment
    and matching braces to produce a full JSON object.
    """
    m = re.search(r'window\.appLocale\s*=\s*', page_html)
    if not m:
        return {}
    start = page_html.find('{', m.end())
    if start == -1:
        return {}
    depth = 0
    for i in range(start, len(page_html)):
        ch = page_html[i]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                json_text = page_html[start:i+1]
                try:
                    return json.loads(json_text)
                except Exception:
                    return {}
    return {}


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

    # Robustly assert drop-zone presence: ensure element with id="dropZone" exists
    # and that its class list includes "drop-zone" (do not require exact attribute ordering)
    import re

    m = re.search(r"<[^>]*id=['\"]dropZone['\"][^>]*>", html)
    assert m is not None, 'dropZone element not found in homepage HTML'

    # Attributes may appear in any order; extract the full tag text around the id
    m_id = re.search(r"id=['\"]dropZone['\"]", html)
    assert m_id is not None, 'dropZone id attribute not found'
    tag_start = html.rfind('<', 0, m_id.start())
    tag_end = html.find('>', m_id.end())
    assert tag_start != -1 and tag_end != -1, 'could not extract dropZone tag'
    tag_text = html[tag_start:tag_end+1]
    m_class = re.search(r'class=["\']([^"\']+)["\']', tag_text)
    assert m_class is not None, 'dropZone element missing class attribute'
    classes = m_class.group(1).split()
    assert 'drop-zone' in classes, f'dropZone element classes do not include drop-zone: {classes}'

    assert 'id="chooseFile"' in html


def test_japanese_homepage_uses_translated_trust_and_support_copy():
    client = TestClient(app)
    response = client.get("/?lang=ja")

    assert response.status_code == 200
    html = response.text

    # The app exposes translations via `window.appLocale` (JSON). Decode it and assert
    # the relevant translation values rather than relying on literal text in the HTML.
    app_locale = extract_app_locale(html)

    # Check key translations exist under top-level `trust` with expected Japanese values.
    trust_top = app_locale.get('trust', {}) or {}

    # Strict assertions validate exact top-level trust translations (canonical source).
    assert trust_top.get('secure_processing') == '安全な処理'
    assert trust_top.get('browser_based') == 'ブラウザベース'
    assert trust_top.get('fast_conversion') == '高速変換'
    assert trust_top.get('wide_format') == '幅広いフォーマット対応'


def test_navbar_and_hero_subtitle_are_localized_for_spanish_and_french():
    client = TestClient(app)

    spanish_response = client.get("/?lang=es")
    spanish_html = spanish_response.text
    # parse window.appLocale JSON and assert decoded hero subtitle
    es_locale = extract_app_locale(spanish_html)
    # hero secondary translation lives under `hero.description_secondary`
    es_hero_secondary = (es_locale.get('hero') or {}).get('description_secondary')
    assert es_hero_secondary == 'que soporta más de 100 formatos.'

    french_response = client.get("/?lang=fr")
    french_html = french_response.text
    fr_locale = extract_app_locale(french_html)
    fr_hero_secondary = (fr_locale.get('hero') or {}).get('description_secondary')
    assert fr_hero_secondary == 'qui prend en charge plus de 100 formats.'


def test_indonesian_hero_subtitle_uses_full_translation_without_english_tail():
    client = TestClient(app)
    response = client.get("/?lang=id")

    assert response.status_code == 200
    html = response.text

    assert 'yang mendukung lebih dari 100 format.' in html
    assert 'that supports 100+ formats.' not in html


def test_jpg_to_pdf_landing_page_renders_localized_text_and_frontend_locale():
    client = TestClient(app)
    # legacy root retired — canonical tool route
    english_response = client.get("/tools/jpg-to-pdf")
    assert english_response.status_code == 200
    english_html = english_response.text

    assert 'lang="en"' in english_html
    assert 'Upload Your File' in english_html
    assert 'Convert now' in english_html
    assert 'window.appLocale' in english_html
    assert 'window.translate = function' in english_html

    indonesian_response = client.get("/tools/jpg-to-pdf?lang=id")
    assert indonesian_response.status_code == 200
    indonesian_html = indonesian_response.text

    assert 'lang="id"' in indonesian_html
    assert 'Unggah File Anda' in indonesian_html
    assert 'Konversi sekarang' in indonesian_html
    assert 'window.appLocale' in indonesian_html
    assert 'window.localeCode = "id"' in indonesian_html
