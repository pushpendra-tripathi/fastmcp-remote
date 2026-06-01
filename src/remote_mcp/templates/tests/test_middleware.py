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


def test_sse_missing_auth_returns_401(client):
    r = client.get("/sse")
    assert r.status_code == 401
    assert r.headers.get("www-authenticate", "").lower().startswith("bearer")
    assert "Authorization" in r.json()["error"]


def test_options_request_passes_through(client):
    r = client.options(
        "/sse",
        headers={
            "Origin": "https://claude.ai",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert r.status_code in (200, 204)
