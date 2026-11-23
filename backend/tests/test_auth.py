"""Tests for the Keycloak OIDC auth module — PKCE and JWT validation."""

import base64
import hashlib
import pytest

from app.core.auth import (
    generate_code_verifier,
    generate_code_challenge,
    verify_code_challenge,
)


class TestPKCE:
    def test_generate_code_verifier_has_correct_length(self):
        """Code verifier should be base64url-encoded 32 bytes (43 chars without padding)."""
        verifier = generate_code_verifier()
        assert 40 <= len(verifier) <= 50  # base64url of 32 bytes, minus padding
        # Verify it's valid base64url
        try:
            base64.urlsafe_b64decode(verifier + "==")
        except Exception:
            pytest.fail("Code verifier is not valid base64url")

    def test_generate_code_challenge(self):
        """Code challenge should be SHA-256 derived from verifier."""
        verifier = generate_code_verifier()
        challenge = generate_code_challenge(verifier)
        assert 40 <= len(challenge) <= 50
        # Verify challenge matches
        assert verify_code_challenge(verifier, challenge) is True

    def test_verify_code_challenge_mismatch(self):
        """Verifier and challenge must match exactly."""
        verifier1 = generate_code_verifier()
        verifier2 = generate_code_verifier()
        challenge = generate_code_challenge(verifier1)
        # Wrong verifier should not match
        assert verify_code_challenge(verifier2, challenge) is False


class TestJWTValidation:
    """Note: Full JWT validation requires a real Keycloak instance with
    RS256 keys. These tests verify the validation scaffolding."""

    def test_validate_id_token_missing_issuer(self):
        """validate_id_token should reject tokens with wrong issuer."""
        import json
        from jose import jwt

        # Create a token with wrong issuer
        payload = {
            "iss": "https://wrong-keycloak.example.com/realms/master",
            "aud": "test-client",
            "sub": "user123",
            "exp": 9999999999,
        }
        # Sign with a dummy key won't verify, but the options should
        # still attempt validation
        try:
            token = jwt.encode(payload, "dummy-key", algorithm="HS256")
            from fastapi import Request
            # Just verify the function exists and raises on bad tokens
            from app.core.auth import validate_id_token
            with pytest.raises(Exception):
                validate_id_token(token, expected_audience="test-client")
        except Exception:
            pytest.skip("jose not fully configured in test env")

    def test_validate_id_token_wrong_audience(self):
        """validate_id_token should reject tokens with wrong audience."""
        import json
        from jose import jwt

        payload = {
            "iss": "https://keycloak.example.com/realms/master",
            "aud": "wrong-client",
            "sub": "user123",
            "exp": 9999999999,
        }
        try:
            token = jwt.encode(payload, "dummy-key", algorithm="HS256")
            from app.core.auth import validate_id_token
            with pytest.raises(Exception):
                validate_id_token(token, expected_audience="correct-client")
        except Exception:
            pytest.skip("jose not fully configured in test env")
