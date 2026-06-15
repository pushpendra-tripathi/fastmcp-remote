import pytest


@pytest.fixture
def client(test_client):
    return test_client


def test_health_bypasses_auth(client):
    r = client.get("/health")
    assert r.status_code == 200


def test_well_known_bypasses_auth(client):
    r = client.get("/.well-known/oauth-authorization-server")
    assert r.status_code == 200


def test_root_ui_bypasses_auth(client):
    r = client.get("/")
    assert r.status_code != 401


def test_mcp_missing_auth_returns_401(client):
    r = client.get("/mcp")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("bearer")
    assert "Authorization" in r.json()["error"]


def test_options_request_passes_through(client):
    r = client.options(
        "/mcp",
        headers={
            "Origin": "https://claude.ai",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert r.status_code in (200, 204)


def test_auth_mode_none_allows_unauthenticated(client, monkeypatch):
    from src.config.settings import settings

    monkeypatch.setattr(settings, "auth_mode", "none")
    r = client.get("/mcp")
    assert r.status_code != 401


def test_401_includes_resource_metadata(client):
    r = client.get("/mcp")
    assert r.status_code == 401
    www = r.headers.get("www-authenticate", "")
    assert 'resource_metadata="' in www
    assert "/.well-known/oauth-protected-resource" in www


def test_disallowed_origin_gets_403(client):
    r = client.get("/mcp", headers={"Origin": "https://evil.example.com"})
    assert r.status_code == 403


def test_allowed_origin_passes_origin_check(client):
    # claude.ai is in the default ALLOWED_ORIGINS; still 401 (no token), not 403.
    r = client.get("/mcp", headers={"Origin": "https://claude.ai"})
    assert r.status_code == 401
