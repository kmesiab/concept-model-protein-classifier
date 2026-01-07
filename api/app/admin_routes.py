"""
Admin API routes for audit log queries and system management.

Provides endpoints for:
- Querying usage audit logs
- Admin-level operations
"""

import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from fastapi import status as http_status

from .audit_log_service import get_audit_log_service
from .models import AuditLogEntry, AuditLogsResponse, ErrorResponse
from .rate_limiter import get_rate_limiter
from .session_service import get_session_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


def _anonymize_email(email: str) -> str:
    """
    Create a non-PII anonymized identifier from an email address.

    Args:
        email: User's email address

    Returns:
        Anonymized identifier (first 16 chars of SHA-256 hash for 64 bits of entropy)
    """
    return hashlib.sha256(email.encode()).hexdigest()[:16]


async def get_current_admin_user(
    authorization: Optional[str] = Header(None),
) -> str:
    """
    Dependency to get the current authenticated admin user's email from JWT token.

    For now, all authenticated users have admin access.
    In production, this should check for admin role/permissions.

    Args:
        authorization: Authorization header with Bearer token

    Returns:
        User's email address

    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header. Include 'Authorization: Bearer <token>' header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse Bearer token
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Verify token
    session_service = get_session_service()
    payload = session_service.verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=http_status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # TODO: Add role/permission check for admin access
    # For now, all authenticated users can access admin endpoints
    # In production, check payload for admin role or query user permissions

    return payload["email"]


async def check_admin_rate_limit(request: Request):
    """
    Rate limit dependency for admin endpoints.

    Limits to 10 requests per minute per user to prevent abuse.
    """
    rate_limiter = get_rate_limiter()

    # Use IP address as identifier for rate limiting
    client_ip = request.client.host if request.client else "unknown"
    ip_hash = hashlib.sha256(client_ip.encode()).hexdigest()[:16]

    # Check rate limit: 10 admin requests per minute per IP
    # Note: max_sequences_per_day is a legacy parameter name from the rate limiter
    # but is being used here as a daily request limit (not sequence limit)
    allowed, error_msg, error_details = rate_limiter.check_rate_limit(
        api_key_hash=f"admin:{ip_hash}",
        max_requests_per_minute=10,
        max_sequences_per_day=1000,  # Used as daily request limit (legacy parameter name)
        num_sequences=1,  # Increment by 1 request
    )

    if not allowed:
        raise HTTPException(
            status_code=http_status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg or "Too many admin requests. Please try again in a minute.",
        )


@router.get(
    "/audit-logs",
    response_model=AuditLogsResponse,
    summary="Query API usage audit logs",
    responses={
        200: {"description": "Audit logs retrieved successfully"},
        400: {"description": "Invalid request parameters", "model": ErrorResponse},
        401: {"description": "Authentication required", "model": ErrorResponse},
        429: {"description": "Rate limit exceeded", "model": ErrorResponse},
    },
    dependencies=[Depends(check_admin_rate_limit)],
)
async def get_audit_logs(
    start_time: str = Query(..., description="Start of query window (ISO 8601)"),
    end_time: str = Query(..., description="End of query window (ISO 8601)"),
    api_key_id: Optional[str] = Query(None, description="Filter by specific API key ID"),
    status: Optional[str] = Query(None, description="Filter by status (success/error)"),
    limit: int = Query(100, ge=1, le=1000, description="Results per page (max 1000)"),
    next_token: Optional[str] = Query(None, description="Pagination token"),
    current_user: str = Depends(get_current_admin_user),
):
    """
    Query API usage audit logs for authorized admins.

    **Query Parameters:**
    - `start_time`: ISO 8601 timestamp (required)
    - `end_time`: ISO 8601 timestamp (required)
    - `api_key_id`: Filter by specific API key ID (optional)
    - `status`: Filter by 'success' or 'error' (optional)
    - `limit`: Results per page, default 100, max 1000
    - `next_token`: For pagination (optional)

    **Security & Privacy:**
    - Only metadata returned (never sequence content)
    - API keys masked except last 4 chars
    - Admins can only query their own org's logs (currently: own email)
    - 30-day retention window
    - Access is logged for security auditing

    **Rate Limits:**
    - 10 queries per minute per admin account

    **Authentication Required:**
    - Must include valid JWT access token in Authorization header
    - Format: `Authorization: Bearer <access_token>`
    """
    # Parse timestamps - handle various ISO 8601 formats
    try:
        # Handle 'Z' suffix for UTC
        start_time_normalized = start_time.replace("Z", "+00:00")
        end_time_normalized = end_time.replace("Z", "+00:00")

        # Parse timestamps - fromisoformat requires timezone-aware strings in Python 3.11+
        start_dt = datetime.fromisoformat(start_time_normalized)
        end_dt = datetime.fromisoformat(end_time_normalized)

        # Ensure timestamps are timezone-aware (convert naive to UTC if needed)
        if start_dt.tzinfo is None:
            start_dt = start_dt.replace(tzinfo=timezone.utc)
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

    except (ValueError, AttributeError) as e:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timestamp format. Use ISO 8601 format (e.g., '2024-01-01T00:00:00Z' or '2024-01-01T00:00:00+00:00'): {str(e)}",
        ) from e

    # Validate time range
    if start_dt >= end_dt:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="start_time must be before end_time",
        )

    # Validate status filter
    if status and status not in ["success", "error"]:
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail="status must be 'success' or 'error'",
        )

    # Query audit logs
    audit_log_service = get_audit_log_service()

    try:
        logs, new_next_token = audit_log_service.query_logs(
            user_email=current_user,
            start_time=start_dt,
            end_time=end_dt,
            api_key_id=api_key_id,
            status=status,
            limit=limit,
            next_token=next_token,
        )

        # Log admin access for security auditing (not in audit log table to avoid pollution)
        logger.info(
            "Admin %s queried audit logs: %d results (time range: %s to %s)",
            _anonymize_email(current_user),
            len(logs),
            start_time,
            end_time,
        )

        return AuditLogsResponse(
            logs=[AuditLogEntry(**log) for log in logs],
            total=len(logs),
            next_token=new_next_token,
        )

    except ClientError as e:
        logger.error("Failed to query audit logs due to DynamoDB error: %s", str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to query audit logs",
        ) from e
    except ValueError as e:
        # Re-raise validation errors as 400 Bad Request
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
