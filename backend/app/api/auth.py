"""Auth routes for Keycloak OIDC authorization-code login with PKCE."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from starlette.responses import JSONResponse

from ..core.auth import (
    generate_code_verifier,
    generate_code_challenge,
    verify_code_challenge,
    validate_id_token,
    get_current_user,
    require_role,
    require_any_role,
)
from ..core.config import settings

router = APIRouter(prefix="/api/v1", tags=["auth"])


@router.get("/login")
def login(request: Request) -> JSONResponse:
    """Initiate Keycloak OIDC authorization-code flow with PKCE.

    Generates a PKCE code verifier / challenge, stores the verifier in a
    short-lived cookie, and redirects the user to Keycloak's authorize URL.
    """
    code_verifier = generate_code_verifier()
    code_challenge = generate_code_challenge(code_verifier)

    # Store verifier in session for verification at callback
    request.session["keycloak_code_verifier"] = code_verifier

    # Build the authorization request parameters
    params = {
        "response_type": "code",
        "client_id": settings.keycloak_client_id or "cobalt-foundry",
        "redirect_uri": settings.keycloak_redirect_url
        or f"http://{request.client.host}:{request.url.port or 8000}/api/v1/auth/callback",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
        "scope": "openid profile email",
    }

    import urllib.parse

    authorize_url = (
        f"{settings.keycloak_url.rstrip('/')}/realms/"
        f"{settings.keycloak_realm or 'master'}/protocol/openid/authorize?"
        + urllib.parse.urlencode(params)
    )

    return JSONResponse({"authorize_url": authorize_url})


@router.get("/callback")
async def auth_callback(request: Request) -> JSONResponse:
    """Handle the Keycloak OIDC callback with the authorization code.

    Exchanges the authorization code for tokens, validates the id_token,
    and sets a session cookie with the user's identity.
    """
    code = request.query_params.get("code")
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Missing authorization code in callback",
        )

    # Retrieve the PKCE verifier that was stored during login
    stored_verifier = request.session.get("keycloak_code_verifier")
    if not stored_verifier:
        raise HTTPException(
            status_code=400,
            detail="PKCE verifier missing or expired",
        )

    # Exchange the authorization code for tokens at Keycloak token endpoint
    token_url = (
        f"{settings.keycloak_url.rstrip('/')}/realms/"
        f"{settings.keycloak_realm or 'master'}/protocol/openid/token"
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(token_url, data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.keycloak_redirect_url
            or f"http://{request.client.host}:{request.url.port or 8000}/api/v1/auth/callback",
            "client_id": settings.keycloak_client_id or "cobalt-foundry",
            "code_verifier": stored_verifier,
        })
        if resp.status_code != 200:
            raise HTTPException(
                status_code=400,
                detail=f"Token exchange failed: {resp.text}",
            )
        tokens = resp.json()

    id_token = tokens.get("id_token")
    if not id_token:
        raise HTTPException(
            status_code=400,
            detail="No id_token received from Keycloak",
        )

    # Validate the id_token (checks issuer, audience, signature)
    payload = validate_id_token(id_token, expected_audience=settings.keycloak_client_id)

    return JSONResponse({"detail": "login successful", "user": dict(payload)})


@router.post("/logout")
def logout(request: Request) -> JSONResponse:
    """Logout endpoint — clears the id_token cookie and redirects to
    Keycloak's end-session endpoint."""
    response = JSONResponse({"detail": "logged out"})
    response.delete_cookie("keycloak_id_token")
    return response


@router.get("/me",)
def me(current_user: dict = Depends(get_current_user)) -> dict:
    """Return the current authenticated user's claims payload."""
    return current_user
