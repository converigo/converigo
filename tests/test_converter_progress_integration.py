from pathlib import Path


def test_converter_controller_manages_progress_ui():
    converter_js = Path("app/static/js/convert/converter.js").read_text(encoding="utf-8")

    assert "this.startProgress();" in converter_js
    assert "this.stopProgress(wasSuccess);" in converter_js
    assert "this.setProgress(100);" in converter_js
    assert "window.translate('upload.conversion_failed_try_another'" in converter_js
    assert "window.translate('upload.ready_to_download'" in converter_js


def test_app_js_does_not_duplicate_conversion_handler_when_converter_is_active():
    app_js = Path("app/static/js/app.js").read_text(encoding="utf-8")

    assert "convertBtn.addEventListener(\"click\"" not in app_js
    assert "hasConverterController()" in app_js
