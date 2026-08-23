from pathlib import Path


def test_public_seo_service_exists_and_uses_root_canonical_urls():
    from app.services.public_seo_service import build_public_meta

    meta = build_public_meta("/learning/what-is-png", "What is PNG?", "Learn about PNG files.")

    assert meta["canonical"] == "https://converigo.com/learning/what-is-png"
    assert meta["og_url"] == "https://converigo.com/learning/what-is-png"
    assert "?lang=" not in meta["canonical"]


def test_public_seo_strips_lang_query_params_from_canonical_urls():
    from app.services.public_seo_service import build_public_meta

    meta = build_public_meta("/?lang=ja", "Converigo", "Convert files online.")

    assert meta["canonical"] == "https://converigo.com/"
    assert meta["og_url"] == "https://converigo.com/"
    assert "?lang=" not in meta["canonical"]


def test_public_seo_keeps_canonical_url_without_query_string_when_passed_as_full_url():
    from app.services.public_seo_service import build_public_meta

    meta = build_public_meta("https://converigo.com/tools/jpg-to-pdf?lang=es", "JPG to PDF", "Convert JPG to PDF.")

    assert meta["canonical"] == "https://converigo.com/tools/jpg-to-pdf"
    assert "?lang=" not in meta["canonical"]


def test_active_home_template_uses_public_seo_partial():
    page = Path("app/templates/main/converigo_main.html").read_text(encoding="utf-8")

    assert 'partials/public_seo_meta.html' in page
    assert 'partials/seo_meta.html' not in page
