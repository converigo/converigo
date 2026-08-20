from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from app.services.seo_service import SeoService

class DummyState:
    def __init__(self, lang_code='en'):
        self.locale = {'lang_code': lang_code}
        self.t = lambda *a, **k: a[0]
        self.supported_locales = ['en', 'id', 'es', 'fr', 'ja']
        self.verification_token = ''
        self.bing_verification_token = ''

class DummyURL:
    def __init__(self, path='/'):
        self.path = path

class DummyRequest:
    def __init__(self, state, path='/'):
        self.state = state
        self.url = DummyURL(path)

def test_homepage_canonical_root():
    svc = SeoService(Path('app/data'))
    req = DummyRequest(DummyState('en'), '/')
    meta = svc.build_home_meta(req)
    assert meta['canonical'].rstrip('/') == 'https://converigo.com'

def test_homepage_hreflang_and_xdefault_rendering():
    svc = SeoService(Path('app/data'))
    state = DummyState('en')
    req = DummyRequest(state, '/')
    meta = svc.build_home_meta(req)

    # Render seo_meta.html partial using Jinja2 with minimal context
    env = Environment(loader=FileSystemLoader('app/templates'))
    tmpl = env.get_template('partials/seo_meta.html')

    rendered = tmpl.render(meta=meta, seo=meta, request=req)

    # Check canonical link
    assert '<link rel="canonical" href="https://converigo.com/">' in rendered

    # Check hreflang alternates for en,id,es,fr,ja and x-default
    for hl in ['en','id','es','fr','ja']:
        assert f'hreflang="{hl}"' in rendered
    assert 'hreflang="x-default"' in rendered

def test_non_homepage_canonical_unchanged():
    svc = SeoService(Path('app/data'))
    req = DummyRequest(DummyState('en'), '/tools/mp4-to-mp3')
    tool_meta = svc.build_tool_meta(req, {'slug':'mp4-to-mp3','title':'MP4 to MP3'})
    assert '/tools/mp4-to-mp3' in tool_meta['canonical'] or 'mp4-to-mp3' in tool_meta['canonical']
