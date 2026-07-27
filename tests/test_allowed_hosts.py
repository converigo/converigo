from app.core.settings import Settings


def test_settings_default_allowed_hosts_include_converigo_domains(monkeypatch):
    # Ensure env var is not present, then instantiate a fresh Settings
    # object instead of reloading the module to avoid polluting global state.
    monkeypatch.delenv("ALLOWED_HOSTS", raising=False)

    settings = Settings()
    hosts = settings.ALLOWED_HOSTS

    assert "localhost" in hosts
    assert "127.0.0.1" in hosts
    assert "converigo.com" in hosts
    assert "www.converigo.com" in hosts
