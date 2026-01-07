"""
Audit log service for tracking API usage and security events.

Provides functionality to:
- Log API requests with metadata
- Query audit logs with filtering and pagination
- Enforce data retention policies
"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class AuditLogService:
    """
    Manages audit logs for API usage tracking and compliance.

    Logs include request metadata like timestamps, API keys,
    processing times, and status codes. Logs are stored in DynamoDB
    with automatic 30-day retention via TTL.
    """

    def __init__(
        self,
        table_name: Optional[str] = None,
        region_name: Optional[str] = None,
    ):
        """
        Initialize the audit log service.

        Args:
            table_name: DynamoDB table name for audit logs
            region_name: AWS region
        """
        self.table_name = table_name or os.getenv(
            "DYNAMODB_USAGE_AUDIT_TABLE", "protein-classifier-usage-audit-logs"
        )
        region = region_name or os.getenv("AWS_REGION", "us-west-2")

        # Initialize DynamoDB client
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(self.table_name)

        # Retention period in days
        self.retention_days = 30

    def log_request(
        self,
        api_key: Optional[str],
        api_key_id: Optional[str],
        user_email: Optional[str],
        sequence_length: int,
        processing_time_ms: float,
        status: str,
        error_code: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> None:
        """
        Log an API request for audit purposes.

        Args:
            api_key: Full API key (will be hashed for storage)
            api_key_id: API key ID for queries
            user_email: User's email address (for org filtering)
            sequence_length: Total length of sequences processed
            processing_time_ms: Processing time in milliseconds
            status: Request status ('success' or 'error')
            error_code: Optional error code if request failed
            ip_address: Client IP address (will be masked for privacy)
        """
        timestamp = int(time.time())
        timestamp_iso = datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()

        # Create unique event ID
        event_id = f"{timestamp}_{secrets.token_hex(8)}"

        # Hash API key for storage (never store plaintext)
        api_key_hash = self._hash_key(api_key) if api_key else "anonymous"

        # Mask last 4 chars of API key for display
        masked_key = self._mask_api_key(api_key) if api_key else "anonymous"

        # Mask IP address for privacy (keep first 3 octets)
        masked_ip = self._mask_ip(ip_address) if ip_address else "unknown"

        # Calculate TTL (30 days from now)
        expires_at = timestamp + (self.retention_days * 24 * 60 * 60)

        try:
            self.table.put_item(
                Item={
                    "event_id": event_id,
                    "timestamp": timestamp,
                    "timestamp_iso": timestamp_iso,
                    "api_key_hash": api_key_hash,
                    "api_key_id": api_key_id or "anonymous",
                    "user_email": user_email or "anonymous@example.com",
                    "masked_api_key": masked_key,
                    "sequence_length": sequence_length,
                    "processing_time_ms": float(processing_time_ms),
                    "status": status,
                    "error_code": error_code,
                    "ip_address": masked_ip,
                    "expires_at": expires_at,
                }
            )
        except ClientError as e:
            # Non-critical error, log but don't fail the request
            logger.warning(f"Failed to create audit log: {e}")

    def query_logs(
        self,
        user_email: str,
        start_time: datetime,
        end_time: datetime,
        api_key_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
        next_token: Optional[str] = None,
    ) -> Tuple[List[Dict], Optional[str]]:
        """
        Query audit logs with filtering and pagination.

        Args:
            user_email: User's email (for org-level filtering)
            start_time: Start of query window
            end_time: End of query window
            api_key_id: Optional filter by specific API key
            status: Optional filter by status ('success' or 'error')
            limit: Maximum results per page (default 100, max 1000)
            next_token: Pagination token from previous query

        Returns:
            Tuple of (log_entries, next_token)
        """
        # Validate and cap limit
        limit = min(max(1, limit), 1000)

        # Convert datetimes to Unix timestamps
        start_ts = int(start_time.timestamp())
        end_ts = int(end_time.timestamp())

        try:
            # Build query parameters
            query_params: Dict = {
                "IndexName": "UserEmailTimestampIndex",
                "KeyConditionExpression": Key("user_email").eq(user_email)
                & Key("timestamp").between(start_ts, end_ts),
                "Limit": limit,
                "ScanIndexForward": False,  # Most recent first
            }

            # Add pagination token if provided
            if next_token:
                try:
                    # Decode the pagination token
                    decoded_token = json.loads(next_token)
                    query_params["ExclusiveStartKey"] = decoded_token
                except (json.JSONDecodeError, ValueError):
                    logger.warning("Invalid pagination token provided")
                    # Continue without pagination

            # Execute query
            response = self.table.query(**query_params)

            items = response.get("Items", [])

            # Apply additional filters
            filtered_items = items
            if api_key_id:
                filtered_items = [
                    item for item in filtered_items if item.get("api_key_id") == api_key_id
                ]
            if status:
                filtered_items = [item for item in filtered_items if item.get("status") == status]

            # Convert to response format
            log_entries = []
            for item in filtered_items:
                log_entries.append(
                    {
                        "timestamp": item.get("timestamp_iso", ""),
                        "api_key": item.get("masked_api_key", "****"),
                        "sequence_length": int(item.get("sequence_length", 0)),
                        "processing_time_ms": float(item.get("processing_time_ms", 0.0)),
                        "status": item.get("status", "unknown"),
                        "error_code": item.get("error_code"),
                        "ip_address": item.get("ip_address", "unknown"),
                    }
                )

            # Create next token if there are more results
            new_next_token = None
            if "LastEvaluatedKey" in response:
                new_next_token = json.dumps(response["LastEvaluatedKey"])

            return log_entries, new_next_token

        except ClientError as e:
            logger.error(f"Failed to query audit logs: {e}")
            raise

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash an API key for secure storage."""
        if not api_key:
            return "anonymous"
        return hashlib.sha256(api_key.encode()).hexdigest()

    @staticmethod
    def _mask_api_key(api_key: str) -> str:
        """Mask API key showing only last 4 characters."""
        if not api_key or len(api_key) < 4:
            return "****"
        return f"****{api_key[-4:]}"

    @staticmethod
    def _mask_ip(ip_address: str) -> str:
        """
        Mask IP address for privacy.

        Keeps first 3 octets for IPv4, first 3 hextets for IPv6.
        """
        if not ip_address:
            return "unknown"

        # Handle IPv4
        if "." in ip_address:
            parts = ip_address.split(".")
            if len(parts) == 4:
                return f"{parts[0]}.{parts[1]}.{parts[2]}.0/24"

        # Handle IPv6
        if ":" in ip_address:
            parts = ip_address.split(":")
            if len(parts) >= 3:
                return f"{parts[0]}:{parts[1]}:{parts[2]}::/48"

        return ip_address


# Global instance
_audit_log_service: Optional[AuditLogService] = None


def get_audit_log_service() -> AuditLogService:
    """Get or create the audit log service instance."""
    global _audit_log_service
    if _audit_log_service is None:
        _audit_log_service = AuditLogService()
    return _audit_log_service
