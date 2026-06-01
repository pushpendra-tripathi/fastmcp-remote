import pytest

from src.core.auth import extract_bearer_token


class _MockRequest:
    def __init__(self, headers):
        self.headers = headers


class _MockRequestContext:
    def __init__(self, headers):
        self.request = _MockRequest(headers)


class _MockContext:
    def __init__(self, headers):
        self.request_context = _MockRequestContext(headers)


def test_extract_bearer_token_valid():
    ctx = _MockContext({"authorization": "Bearer mytoken123"})
    result = extract_bearer_token(ctx)
    assert result == "Bearer mytoken123"


def test_extract_bearer_token_missing_header():
    ctx = _MockContext({})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_malformed_scheme():
    ctx = _MockContext({"authorization": "Basic sometoken"})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_empty_bearer():
    ctx = _MockContext({"authorization": "Bearer "})
    with pytest.raises(ValueError, match="Missing Authorization header"):
        extract_bearer_token(ctx)


def test_extract_bearer_token_case_insensitive_header():
    ctx = _MockContext({"Authorization": "Bearer MYTOKEN"})
    result = extract_bearer_token(ctx)
    assert result == "Bearer MYTOKEN"
