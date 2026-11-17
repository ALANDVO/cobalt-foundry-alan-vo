API routes for OIDC authentication.
from fastapi import APIRouter
router = APIRouter(prefix="/auth", tags=["auth"])

@router.get("/login")
def login(): return {"message": "Login not implemented yet"}

@router.get("/callback")
def callback(): return {"message": "Callback not implemented yet"}

@router.get("/logout")
def logout(): return {"message": "Logout not implemented yet"}