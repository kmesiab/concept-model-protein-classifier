"""
API routes for API key management (self-service portal).

Provides endpoints for:
- Registering new API keys
- Listing user's API keys
- Rotating API keys
- Revoking API keys
"""

import hashlib
import logging
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status

from .api_key_service import get_api_key_service
from .email_service import get_email_service
from .models import (
    APIKeyInfo,
    APIKeyResponse,
    ErrorResponse,
    ListAPIKeysResponse,
    RegisterAPIKeyRequest,
    RevokeAPIKeyRequest,
    RevokeAPIKeyResponse,
    RotateAPIKeyRequest,
)
from .session_service import get_session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/api-keys", tags=["API Key Management"])


def _anonymize_email(email: str) -> str:
    """
    Create a non-PII anonymized identifier from an email address.

    Args:
        email: User's email address

    Returns:
        Anonymized identifier (first 8 chars of SHA-256 hash)
    """
    return hashlib.sha256(email.encode()).hexdigest()[:8]


async def get_current_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Dependency to get the current authenticated user's email from JWT token.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User's email address

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Missing authorization header. " "Include 'Authorization: Bearer <token>' header."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify token
    session_service = get_session_service()
    payload = session_service.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return payload["email"]


@router.post(
    "/register",
    response_model=APIKeyResponse,
    summary="Register a new API key",
    responses={
        200: {"description": "API key created successfully"},
        401: {"description": "Authentication required", "model": ErrorResponse},
        400: {"description": "Invalid request", "model": ErrorResponse},
    },
)
async def register_api_key(
    request: RegisterAPIKeyRequest, current_user: str = Depends(get_current_user)
):
    """
    Generate a new API key for the authenticated user.

    **Important:**
    - The API key value is only shown once and cannot be retrieved later
    - Store the API key securely immediately after creation
    - The key is active immediately upon creation

    **Authentication Required:**
    - Must include valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    api_key_service = get_api_key_service()

    # Generate API key
    result = api_key_service.generate_api_key(
        user_email=current_user, label=request.label, tier="free"
    )

    # Send notification email
    email_service = get_email_service()
    await email_service.send_api_key_created_notification(
        current_user, result["api_key_id"], result["label"]
    )

    logger.info("API key registered for user %s", _anonymize_email(current_user))

    return APIKeyResponse(**result)


@router.get(
    "/list",
    response_model=ListAPIKeysResponse,
    summary="List all API keys",
    responses={
        200: {"description": "API keys retrieved successfully"},
        401: {"description": "Authentication required", "model": ErrorResponse},
    },
)
async def list_api_keys(current_user: str = Depends(get_current_user)):
    """
    List all API keys for the authenticated user.

    Returns both active and revoked keys with metadata.
    **Note:** The actual API key values are never returned, only metadata.

    **Authentication Required:**
    - Must include valid JWT access token in Authorization header
    """
    api_key_service = get_api_key_service()
    keys = api_key_service.list_api_keys(current_user)

    return ListAPIKeysResponse(keys=[APIKeyInfo(**key) for key in keys], total=len(keys))


@router.post(
    "/rotate",
    response_model=APIKeyResponse,
    summary="Rotate an API key",
    responses={
        200: {"description": "API key rotated successfully"},
        401: {"description": "Authentication required", "model": ErrorResponse},
        403: {"description": "Permission denied", "model": ErrorResponse},
        404: {"description": "API key not found", "model": ErrorResponse},
    },
)
async def rotate_api_key(
    request: RotateAPIKeyRequest, current_user: str = Depends(get_current_user)
):
    """
    Rotate an existing API key.

    Creates a new API key and immediately revokes the old one.
    The new key is active immediately.

    **Important:**
    - The new API key value is only shown once
    - The old key is revoked immediately
    - Update your applications with the new key

    **Authentication Required:**
    - Must include valid JWT access token in Authorization header
    - Can only rotate your own API keys
    """
    api_key_service = get_api_key_service()

    try:
        result = api_key_service.rotate_api_key(current_user, request.api_key_id)
        logger.info(
            "API key %s rotated for user %s",
            request.api_key_id,
            _anonymize_email(current_user),
        )
        return APIKeyResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e


@router.post(
    "/revoke",
    response_model=RevokeAPIKeyResponse,
    summary="Revoke an API key",
    responses={
        200: {"description": "API key revoked successfully"},
        401: {"description": "Authentication required", "model": ErrorResponse},
        403: {"description": "Permission denied", "model": ErrorResponse},
        404: {"description": "API key not found", "model": ErrorResponse},
    },
)
async def revoke_api_key(
    request: RevokeAPIKeyRequest, current_user: str = Depends(get_current_user)
):
    """
    Permanently revoke an API key.

    The key will become inactive and cannot be used for API requests.
    Revocation takes effect within 5 minutes system-wide.

    **Warning:**
    - This action cannot be undone
    - Applications using this key will immediately lose access

    **Authentication Required:**
    - Must include valid JWT access token in Authorization header
    - Can only revoke your own API keys
    """
    api_key_service = get_api_key_service()

    try:
        api_key_service.revoke_api_key(current_user, request.api_key_id)

        # Get key info for notification
        keys = api_key_service.list_api_keys(current_user)
        revoked_key = next((k for k in keys if k["api_key_id"] == request.api_key_id), None)

        if revoked_key:
            # Send notification email
            email_service = get_email_service()
            await email_service.send_api_key_revoked_notification(
                current_user, request.api_key_id, revoked_key["label"]
            )

        logger.info(
            "API key %s revoked for user %s",
            request.api_key_id,
            _anonymize_email(current_user),
        )

        return RevokeAPIKeyResponse(revoked=True, api_key_id=request.api_key_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from e
