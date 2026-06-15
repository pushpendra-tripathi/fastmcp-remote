import datetime

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from src.config.settings import settings
from src.core.auth import extract_bearer_token, verify_jwt


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


def _rsa_pair():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    return private_pem, public_pem


def _make_token(private_pem, **overrides):
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = {
        "iss": settings.oauth_issuer_url.rstrip("/"),
        "aud": settings.jwt_audience or settings.mcp_public_url,
        "exp": now + datetime.timedelta(minutes=5),
        "iat": now,
        "sub": "user-1",
    }
    claims.update(overrides)
    return pyjwt.encode(claims, private_pem, algorithm="RS256")


def test_verify_jwt_valid():
    private_pem, public_pem = _rsa_pair()
    claims = verify_jwt(_make_token(private_pem), signing_key=public_pem)
    assert claims["sub"] == "user-1"


def test_verify_jwt_rejects_wrong_audience():
    private_pem, public_pem = _rsa_pair()
    token = _make_token(private_pem, aud="https://other.example.com")
    with pytest.raises(pyjwt.PyJWTError):
        verify_jwt(token, signing_key=public_pem)


def test_verify_jwt_rejects_expired():
    private_pem, public_pem = _rsa_pair()
    past = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
    token = _make_token(private_pem, exp=past)
    with pytest.raises(pyjwt.PyJWTError):
        verify_jwt(token, signing_key=public_pem)


def test_verify_jwt_rejects_bad_signature():
    private_pem, _ = _rsa_pair()
    _, other_public = _rsa_pair()
    token = _make_token(private_pem)
    with pytest.raises(pyjwt.PyJWTError):
        verify_jwt(token, signing_key=other_public)


def test_verify_jwt_rejects_missing_exp():
    """A token without exp must be rejected, not treated as never-expiring."""
    private_pem, public_pem = _rsa_pair()
    now = datetime.datetime.now(datetime.timezone.utc)
    claims = {
        "iss": settings.oauth_issuer_url.rstrip("/"),
        "aud": settings.jwt_audience or settings.mcp_public_url,
        "iat": now,
        "sub": "user-1",
    }
    token = pyjwt.encode(claims, private_pem, algorithm="RS256")
    with pytest.raises(pyjwt.PyJWTError):
        verify_jwt(token, signing_key=public_pem)
