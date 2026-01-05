"""
API routes for authentication (magic link email-based auth).

Provides endpoints for:
- Magic link login (send email)
- Token verification (verify magic link)
- Token refresh
"""

import hashlib
import logging
from typing import Optional

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from .email_service import get_email_service
from .models import (
    ErrorResponse,
    LoginRequest,
    LoginResponse,
    RefreshTokenResponse,
    TokenResponse,
    VerifyTokenRequest,
)
from .rate_limiter import get_rate_limiter
from .session_service import get_session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


async def check_auth_rate_limit(request: Request):
    """
    Rate limit dependency for authentication endpoints.

    Limits to 10 requests per minute per IP address.
    """
    rate_limiter = get_rate_limiter()

    # Use IP address as identifier
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    # Check rate limit: 10 requests per minute
    allowed, _ = rate_limiter.check_rate_limit(
        api_key_hash=f"auth:{ip_hash}",
        max_requests_per_minute=10,
        max_sequences_per_day=1000,  # Daily limit to prevent sustained abuse
        num_sequences=1,
    )

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many authentication requests. Please try again in a minute.",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    summary="Request magic link login",
    responses={
        200: {"description": "Magic link sent successfully"},
        400: {"description": "Invalid email", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
    dependencies=[Depends(check_auth_rate_limit)],
)
async def login(request: LoginRequest):
    """
    Request a magic link for email-based authentication.

    Sends a time-limited magic link to the specified email address.
    The link expires in 15 minutes and can only be used once.

    **Security:**
    - Rate limited to prevent abuse
    - Tokens are single-use
    - Tokens expire after 15 minutes
    """
    # Validate email format
    try:
        valid = validate_email(request.email, check_deliverability=False)
        email = valid.normalized
    except EmailNotValidError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid email: {str(e)}"
        ) from e

    # Create magic link token
    session_service = get_session_service()
    token = session_service.create_magic_link_token(email)

    # Send magic link email
    email_service = get_email_service()
    await email_service.send_magic_link(email, token)

    return LoginResponse(message="Magic link sent to your email", email=email)


@router.post(
    "/verify",
    response_model=TokenResponse,
    summary="Verify magic link and get access token",
    responses={
        200: {"description": "Authentication successful"},
        400: {"description": "Invalid or expired token", "model": ErrorResponse},
    },
)
async def verify_token(request: VerifyTokenRequest):
    """
    Verify a magic link token and create a session.

    Returns JWT access and refresh tokens for authenticated API access.

    **Token Usage:**
    - Access token: Valid for 1 hour, used for API authentication
    - Refresh token: Valid for 30 days, used to get new access tokens
    """
    session_service = get_session_service()

    # Verify magic link token
    email = session_service.verify_magic_link_token(request.token)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired magic link token",
        )

    # Create session and return tokens
    tokens = session_service.create_session(email)

    return TokenResponse(**tokens)


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid refresh token", "model": ErrorResponse},
    },
)
async def refresh_token(x_refresh_token: Optional[str] = Header(None, alias="X-Refresh-Token")):
    """
    Refresh an access token using a refresh token.

    Returns a new access token without requiring re-authentication.

    **Usage:**
    - Send refresh token in X-Refresh-Token header
    - Receive new access token with 1 hour expiration
    """
    if not x_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token. Include 'X-Refresh-Token' header.",
        )

    session_service = get_session_service()
    tokens = session_service.refresh_access_token(x_refresh_token)

    if not tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token"
        )

    return RefreshTokenResponse(**tokens)
