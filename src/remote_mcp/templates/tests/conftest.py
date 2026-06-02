import pytest
from starlette.testclient import TestClient


@pytest.fixture(scope="session")
def test_client():
    """Shared TestClient. FastMCP's session manager forbids multiple lifespans."""
    from src.app import app

    with TestClient(app) as c:
        yield c
