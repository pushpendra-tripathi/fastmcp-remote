import json

import pytest
from src.core.telemetry import TelemetryEvent, hash_token, telemetry_service


def test_hash_token_stable_for_same_token():
    a = hash_token("Bearer abc123")
    b = hash_token("Bearer abc123")
    assert a == b
    assert len(a) == 16


def test_hash_token_different_for_different_tokens():
    assert hash_token("Bearer abc") != hash_token("Bearer def")


def test_hash_token_strips_bearer_prefix():
    assert hash_token("Bearer abc123") == hash_token("abc123")


def test_hash_token_anonymous_for_empty():
    assert hash_token("") == "anonymous"
    assert hash_token("Bearer ") == "anonymous"


def test_hash_token_does_not_contain_raw_token():
    raw = "supersecrettoken_xyz"
    h = hash_token(f"Bearer {raw}")
    assert raw not in h
    assert "Bearer" not in h


def test_event_json_excludes_none_fields():
    e = TelemetryEvent(event_type="connection", user_id="abc", path="/mcp")
    payload = e.model_dump_json(exclude_none=True)
    parsed = json.loads(payload)
    assert parsed["event_type"] == "connection"
    assert "tool_name" not in parsed


@pytest.mark.asyncio
async def test_record_event_no_raise_when_disabled():
    e = TelemetryEvent(event_type="connection", user_id="abc")
    await telemetry_service.record_event(e)
