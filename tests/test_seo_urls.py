from pathlib import Path
from types import SimpleNamespace

from app.services.seo_service import SeoService


class DummyURL:
    def __init__(self, scheme="http", hostname="localhost", port=None):
        self.scheme = scheme
        self.hostname = hostname
        self.port = port


class DummyRequest:
    def __init__(self):
        self.headers = {}
        self.url = DummyURL()


def test_seo_service_uses_production_absolute_urls():
    request = DummyRequest()
    service = SeoService(Path("app/data/converters"))

    meta = service.build_home_meta(request)

    assert meta["canonical"] == "https://converigo.com/"
    assert meta["og_url"] == "https://converigo.com/"
