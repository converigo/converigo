from pathlib import Path


def test_header_template_has_mobile_wrapper_classes():
    header_path = Path("app/templates/components/header.html")
    html = header_path.read_text(encoding="utf-8")

    assert 'class="container header-inner"' in html
    assert 'class="header-right"' in html
    assert 'class="main-nav"' in html
    assert 'class="header-actions"' in html
