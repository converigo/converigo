from pathlib import Path


def test_header_template_has_mobile_wrapper_classes():
    header_path = Path("app/templates/components/header.html")
    html = header_path.read_text(encoding="utf-8")

    assert 'class="container header-inner"' in html
    assert 'class="header-right"' in html
    assert 'class="main-nav"' in html
    assert 'class="header-actions"' in html


def test_header_template_layout_order():
    header_path = Path("app/templates/components/header.html")
    html = header_path.read_text(encoding="utf-8")

    logo_index = html.index('class="logo"')
    nav_index = html.index('class="main-nav"')
    right_index = html.index('class="header-right"')

    assert logo_index < nav_index < right_index


def test_header_template_language_selector_has_icon():
    header_path = Path("app/templates/components/header.html")
    html = header_path.read_text(encoding="utf-8")

    assert 'class="language-switcher"' in html
    assert 'class="language-icon"' in html
    assert '<select id="languageSelect"' in html
