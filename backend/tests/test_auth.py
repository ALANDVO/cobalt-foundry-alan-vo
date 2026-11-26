"""Tests for the Keycloak OIDC auth module — PKCE and JWT validation."""

import base64
import hashlib
import pytest

from app.core.auth import (
    generate_code_verifier,
    generate_code_challenge,
    verify_code_challenge,
    validate_id_token,
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
    """JWT validation in demo mode (Keycloak not configured) and production mode.

    In demo mode, tokens with valid JWT structure are accepted.
    In production mode, full RS256 signature verification and issuer/audience
    validation is performed against Keycloak configuration.
    """

    def test_validate_id_token_demo_mode_valid_token(self):
        """validate_id_token should accept valid tokens in demo mode."""
        # Encode as HS256 (any signature is accepted in demo mode)
        from jose import jwt
        payload = {"sub": "user123", "role": "viewer"}
        token = jwt.encode(payload, "dummy-key", algorithm="HS256")

        # In demo mode (no Keycloak config), valid structure should be accepted
        from unittest.mock import patch
        with patch("app.core.auth.settings.keycloak_url", None):
            with patch("app.core.auth.settings.keycloak_realm", None):
                result = validate_id_token(token, expected_audience="test-client")
                # Should accept the token in demo mode
                assert result is not None
                assert result.get("sub") == "user123"

    def test_validate_id_token_demo_mode_invalid_structure(self):
        """validate_id_token should reject tokens with invalid JWT structure in demo mode."""
        from unittest.mock import patch

        with patch("app.core.auth.settings.keycloak_url", None):
            with patch("app.core.auth.settings.keycloak_realm", None):
                # Empty or malformed token should be rejected
                with pytest.raises(Exception):
                    validate_id_token("not-a-jwt-token", expected_audience="test-client")
                with pytest.raises(Exception):
                    validate_id_token("", expected_audience="test-client")

    def test_validate_id_token_production_mode_rejects_wrong_issuer(self):
        """validate_id_token should reject tokens with wrong issuer in production mode."""
        import json
        from jose import jwt

        # Create a token with wrong issuer
        payload = {
            "iss": "https://wrong-keycloak.example.com/realms/master",
            "aud": "test-client",
            "sub": "user123",
            "exp": 9999999999,
        }
        token = jwt.encode(payload, "dummy-key", algorithm="HS256")

        # In production mode (Keycloak config set), wrong issuer should be rejected
        from unittest.mock import patch
        with patch("app.core.auth.settings.keycloak_url", "https://keycloak.example.com"):
            with patch("app.core.auth.settings.keycloak_realm", "master"):
                try:
                    validate_id_token(token, expected_audience="test-client")
                    # If we get here, the token was unexpectedly accepted
                    pytest.fail("Expected HTTPException for wrong issuer")
                except Exception:
                    # Expected - wrong issuer in production mode
                    pass

    def test_validate_id_token_production_mode_rejects_wrong_audience(self):
        """validate_id_token should reject tokens with wrong audience in production mode."""
        import json
        from jose import jwt

        payload = {
            "iss": "https://keycloak.example.com/realms/master",
            "aud": "wrong-client",
            "sub": "user123",
            "exp": 9999999999,
        }
        token = jwt.encode(payload, "dummy-key", algorithm="HS256")

        # In production mode, wrong audience should be rejected
        from unittest.mock import patch
        with patch("app.core.auth.settings.keycloak_url", "https://keycloak.example.com"):
            with patch("app.core.auth.settings.keycloak_realm", "master"):
                try:
                    validate_id_token(token, expected_audience="correct-client")
                    # If we get here, the token was unexpectedly accepted
                    pytest.fail("Expected HTTPException for wrong audience")
                except Exception:
                    # Expected - wrong audience in production mode
                    pass
