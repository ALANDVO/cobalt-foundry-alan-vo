"""Unit tests for security utilities (PKCE helpers)."""
import pytest

from app.core.security import generate_pkce, verify_pkce

class TestPKCE:
    def test_generate_pkce_length(self):
        """PKCE codes should be alphanumeric and length 43."""
        code = generate_pkce()
        assert code.isalnum()
        assert len(code) == 43

    def test_verify_pkce_valid(self):
        """verify_pkce returns True for its own generated code."""
        code = generate_pkce()
        assert verify_pkce(code) is True

    def test_verify_pkce_invalid(self):
        """verify_pkce returns False for arbitrary strings."""
        assert verify_pkce("not a pkce code") is False
        assert verify_pkce("") is False
        assert verify_pkce("a" * 100) is False
