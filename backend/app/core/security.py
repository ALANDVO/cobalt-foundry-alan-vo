# Placeholder for OIDC auth.
import secrets, string

def generate_pkce():
    return "".join(secrets.choice(string.ascii_letters + string.digits) for _ in range(43))

def verify_pkce(code):
    return isinstance(code, str) and len(code) == 43 and code.isalnum()

__all__ = ["generate_pkce", "verify_pkce"]
