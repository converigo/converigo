import importlib


def test_settings_default_allowed_hosts_include_converigo_domains(monkeypatch):
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)
    import app.core.settings as settings_module

    importlib.reload(settings_module)

    hosts = settings_module.settings.ALLOWED_HOSTS

    assert "localhost" in hosts
    assert "127.0.0.1" in hosts
    assert "converigo.com" in hosts
    assert "www.converigo.com" in hosts
