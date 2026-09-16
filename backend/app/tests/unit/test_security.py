from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.security import (
    InvalidTokenError,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def test_expired_token_is_rejected():
    token = create_access_token(subject="1", expires_delta=timedelta(seconds=-1))
    with pytest.raises(InvalidTokenError):
        decode_token(token)


def test_token_carries_correct_tenant_and_role_claims():
    token = create_access_token(subject="1", role="recruiter", tenant_id="42")
    payload = decode_token(token)
    assert payload["role"] == "recruiter"
    assert payload["tenant_id"] == "42"


def test_token_subject_is_correct():
    token = create_access_token(subject="user-123")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"


def test_token_without_tenant_id_has_no_tenant_claim():
    token = create_access_token(subject="1", role="candidate")
    payload = decode_token(token)
    assert "tenant_id" not in payload


def test_password_hash_round_trip():
    plain = "super-secret-password"
    hashed = hash_password(plain)
    assert hashed != plain
    assert verify_password(plain, hashed) is True


def test_wrong_password_fails_verification():
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_refresh_token_is_different_from_access_token():
    access = create_access_token(subject="1")
    refresh = create_refresh_token(subject="1")
    assert access != refresh


def test_tampered_token_is_rejected():
    token = create_access_token(subject="1")
    tampered = token[:-5] + "XXXXX"
    with pytest.raises(InvalidTokenError):
        decode_token(tampered)
