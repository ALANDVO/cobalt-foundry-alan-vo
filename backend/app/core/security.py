"""Security utilities — placeholder for the OIDC auth milestone (round 2).

This module is intentionally empty. When Keycloak OIDC is implemented, it will
contain:
  - PKCE state/nonce generation and verification
  - JWT token validation (issuer, audience, signature)
  - Role-based authorization helpers (viewer / operator / admin)
  - Local demo mode enforcement (localhost binding, production refusal)

No authentication bypass exists in the current codebase.
"""
# Reserved for round 2 implementation.
__all__ = []