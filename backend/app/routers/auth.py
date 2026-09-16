"""
Minimal dashboard authentication (Day 12, Section 15: "Protect the
ticket dashboard").

MVP approach: a single shared password from DASHBOARD_PASSWORD (.env),
sent as the X-Dashboard-Password header on every dashboard request. Not
enterprise-grade auth, but appropriately scoped for a demo project with
one admin user -- and importantly, the password is never hardcoded in
code, only read from the environment.
"""

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel

from app.config import DASHBOARD_PASSWORD

router = APIRouter()


class LoginRequest(BaseModel):
    password: str


@router.post("/login")
def login(payload: LoginRequest):
    """Used by the frontend login form to verify the password before
    storing it client-side for subsequent dashboard requests."""
    if not DASHBOARD_PASSWORD:
        raise HTTPException(
            status_code=500,
            detail="DASHBOARD_PASSWORD is not set in .env -- dashboard login is not configured.",
        )
    if payload.password != DASHBOARD_PASSWORD:
        raise HTTPException(status_code=401, detail="Incorrect password")
    return {"success": True}


def require_dashboard_auth(x_dashboard_password: str = Header(None)):
    """FastAPI dependency: raises 401 unless the correct password is
    supplied in the X-Dashboard-Password header. Applied to every
    /dashboard/* endpoint."""
    if not DASHBOARD_PASSWORD or x_dashboard_password != DASHBOARD_PASSWORD:
        raise HTTPException(status_code=401, detail="Invalid or missing dashboard password")
