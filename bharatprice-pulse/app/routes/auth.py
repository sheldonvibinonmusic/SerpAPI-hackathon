"""
auth.py — BharatPrice Pulse
Lightweight, deployable authentication routes for kirana and retail sellers.
Supports Google One-Tap, Gmail authentication, and 1-click Kirana demo login.
"""
from __future__ import annotations

import logging
import re
from typing import Any, Dict, Optional

from fastapi import APIRouter, Header, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from app.storage.history import get_history_repo

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(description="Seller email or Gmail address")
    name: Optional[str] = Field(default=None, description="Seller display name or shop name")
    provider: str = Field(default="google", description="Auth provider: google, email, demo")
    avatar_url: Optional[str] = Field(default=None, description="Avatar image URL")


class AuthResponse(BaseModel):
    status: str
    user: Dict[str, Any]


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login or Register Seller",
)
async def login_user(payload: LoginRequest) -> AuthResponse:
    """Register or log in seller using Gmail / Google or Kirana demo account."""
    email = payload.email.strip().lower()
    if not email or "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="A valid email address (e.g. your Gmail) is required.",
        )

    # Clean name or generate from email
    name = (payload.name or "").strip()
    if not name:
        name = email.split("@")[0].replace(".", " ").title()

    avatar_url = payload.avatar_url
    if not avatar_url:
        # Generate default SVG avatar URL using Dicebear initials
        clean_initials = "".join([part[0].upper() for part in name.split()[:2]]) or "BP"
        avatar_url = f"https://api.dicebear.com/7.x/initials/svg?seed={clean_initials}&backgroundColor=f39c12,e67e22,1a5276"

    repo = get_history_repo()
    user_record = await repo.save_user(
        email=email,
        name=name,
        provider=payload.provider,
        avatar_url=avatar_url,
    )

    logger.info(f"User logged in successfully: {email} ({name}) via {payload.provider}")
    return AuthResponse(status="authenticated", user=user_record)


@router.get(
    "/me",
    summary="Get Current User Session",
)
async def get_current_user(
    user_email: Optional[str] = Query(default=None),
    x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"),
) -> Dict[str, Any]:
    """Retrieve profile for the authenticated seller."""
    target_email = user_email or x_user_email
    if not target_email or not target_email.strip():
        return {"authenticated": False, "user": None}

    clean_email = target_email.strip().lower()
    repo = get_history_repo()
    user = await repo.get_user(clean_email)
    if not user:
        return {"authenticated": False, "user": None}

    return {"authenticated": True, "user": user}


@router.post(
    "/logout",
    summary="Logout Seller",
)
async def logout_user() -> Dict[str, str]:
    """Sign out seller session."""
    return {"status": "logged_out"}
