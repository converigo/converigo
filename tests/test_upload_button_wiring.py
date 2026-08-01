from pathlib import Path


def test_home_upload_card_uses_shared_file_input_for_custom_button():
    template_path = Path(__file__).resolve().parents[1] / "app/templates/components/home_upload_card.html"
    html = template_path.read_text(encoding="utf-8")

    assert 'id="chooseFile"' in html
    assert 'id="fileInput"' in html
    assert 'type="file"' in html
