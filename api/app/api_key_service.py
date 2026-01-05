"""
API Key storage and management service using DynamoDB.

This module provides secure API key lifecycle management with:
- Encrypted storage in DynamoDB
- API key generation with secure random tokens
- Rotation and revocation capabilities
- Audit logging
"""

import hashlib
import logging
import os
import secrets
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)


class APIKeyService:
    """
    Manages API keys in DynamoDB with encryption and audit logging.

    API keys are stored with SHA-256 hashing, never in cleartext.
    All operations are audited for security compliance.
    """

    def __init__(
        self,
        table_name: str = None,
        audit_table_name: str = None,
        region_name: str = None,
    ):
        """
        Initialize the API key service.

        Args:
            table_name: DynamoDB table name for API keys
            audit_table_name: DynamoDB table name for audit logs
            region_name: AWS region
        """
        self.table_name = table_name or os.getenv(
            "DYNAMODB_API_KEYS_TABLE", "protein-classifier-api-keys"
        )
        self.audit_table_name = audit_table_name or os.getenv(
            "DYNAMODB_AUDIT_TABLE", "protein-classifier-audit-logs"
        )
        region = region_name or os.getenv("AWS_REGION", "us-west-2")

        # Initialize DynamoDB client
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.table = self.dynamodb.Table(self.table_name)
        self.audit_table = self.dynamodb.Table(self.audit_table_name)

    def generate_api_key(
        self,
        user_email: str,
        label: Optional[str] = None,
        tier: str = "free",
    ) -> Dict[str, str]:
        """
        Generate a new API key for a user.

        Args:
            user_email: User's email address
            label: Optional descriptive label for the key
            tier: Subscription tier ('free' or 'premium')

        Returns:
            Dict with api_key, api_key_id, created_at, and label
        """
        # Generate secure random API key
        api_key = f"pk_live_{secrets.token_urlsafe(32)}"
        api_key_id = f"key_{secrets.token_urlsafe(16)}"
        api_key_hash = self._hash_key(api_key)

        created_at = datetime.now(timezone.utc)
        timestamp = int(created_at.timestamp())

        # Determine tier limits
        if tier == "premium":
            daily_limit = 100000
            rate_limit_per_minute = 1000
            max_batch_size = 500
        else:
            daily_limit = 1000
            rate_limit_per_minute = 100
            max_batch_size = 50

        # Store API key metadata in DynamoDB
        item = {
            "api_key_hash": api_key_hash,
            "api_key_id": api_key_id,
            "user_email": user_email,
            "label": label or "Untitled API Key",
            "tier": tier,
            "status": "active",
            "created_at": timestamp,
            "last_used_at": None,
            "daily_limit": daily_limit,
            "rate_limit_per_minute": rate_limit_per_minute,
            "max_batch_size": max_batch_size,
        }

        try:
            self.table.put_item(Item=item)  # type: ignore[arg-type]
            logger.info(f"Created API key {api_key_id} for user {user_email}")

            # Audit log
            self._audit_log(
                user_email=user_email,
                action="api_key_created",
                api_key_id=api_key_id,
                details={"label": label, "tier": tier},
            )

            return {
                "api_key": api_key,
                "api_key_id": api_key_id,
                "created_at": created_at.isoformat(),
                "label": label or "Untitled API Key",
            }
        except ClientError as e:
            logger.error(f"Failed to create API key: {e}")
            raise

    def validate_api_key(self, api_key: str) -> Optional[Dict]:
        """
        Validate an API key and return its metadata.

        Args:
            api_key: API key to validate

        Returns:
            Metadata dict if valid and active, None otherwise
        """
        if not api_key:
            return None

        api_key_hash = self._hash_key(api_key)

        try:
            response = self.table.get_item(Key={"api_key_hash": api_key_hash})
            item = response.get("Item")

            if not item:
                return None

            # Check if key is active
            if item.get("status") != "active":
                return None

            # Update last_used_at timestamp asynchronously
            self._update_last_used(api_key_hash)

            # Convert Decimal to int for compatibility
            # Type ignore needed for DynamoDB's dynamic return types
            return {
                "email": str(item.get("user_email", "")),
                "tier": str(item.get("tier", "free")),
                "daily_limit": int(item.get("daily_limit", 1000)),  # type: ignore[arg-type]
                "rate_limit_per_minute": int(
                    item.get("rate_limit_per_minute", 100)  # type: ignore[arg-type]
                ),
                "max_batch_size": int(item.get("max_batch_size", 50)),  # type: ignore[arg-type]
                "api_key_id": str(item.get("api_key_id", "")),
            }
        except ClientError as e:
            logger.error(f"Failed to validate API key: {e}")
            return None

    def list_api_keys(self, user_email: str) -> List[Dict]:
        """
        List all API keys for a user.

        Args:
            user_email: User's email address

        Returns:
            List of API key metadata dicts (without actual key values)
        """
        try:
            response = self.table.query(
                IndexName="UserEmailIndex",
                KeyConditionExpression="user_email = :email",
                ExpressionAttributeValues={":email": user_email},
            )

            items = response.get("Items", [])

            results = []
            for item in items:
                created_at_val = item.get("created_at")
                last_used_val = item.get("last_used_at")

                results.append(
                    {
                        "api_key_id": str(item.get("api_key_id", "")),
                        "label": str(item.get("label", "Untitled API Key")),
                        "status": str(item.get("status", "unknown")),
                        "created_at": datetime.fromtimestamp(
                            int(created_at_val) if created_at_val else 0,  # type: ignore[arg-type]
                            tz=timezone.utc,
                        ).isoformat(),
                        "last_used_at": (
                            datetime.fromtimestamp(
                                int(last_used_val), tz=timezone.utc  # type: ignore[arg-type]
                            ).isoformat()
                            if last_used_val
                            else None
                        ),
                        "tier": str(item.get("tier", "free")),
                    }
                )

            return results
        except ClientError as e:
            logger.error(f"Failed to list API keys: {e}")
            raise

    def rotate_api_key(self, user_email: str, api_key_id: str) -> Dict[str, str]:
        """
        Rotate an API key (revoke old, create new).

        Args:
            user_email: User's email address (for authorization)
            api_key_id: ID of the key to rotate

        Returns:
            Dict with new api_key, api_key_id, created_at, and label
        """
        # Find the old key
        old_key = self._get_key_by_id(api_key_id)

        if not old_key:
            raise ValueError(f"API key {api_key_id} not found")

        if old_key["user_email"] != user_email:
            raise PermissionError("You can only rotate your own API keys")

        # Revoke old key
        self.revoke_api_key(user_email, api_key_id)

        # Create new key with same label and tier
        new_key = self.generate_api_key(
            user_email=user_email,
            label=f"{old_key.get('label', 'Untitled')} (Rotated)",
            tier=old_key.get("tier", "free"),
        )

        # Audit log
        self._audit_log(
            user_email=user_email,
            action="api_key_rotated",
            api_key_id=api_key_id,
            details={"new_api_key_id": new_key["api_key_id"]},
        )

        return new_key

    def revoke_api_key(self, user_email: str, api_key_id: str) -> bool:
        """
        Revoke an API key.

        Args:
            user_email: User's email address (for authorization)
            api_key_id: ID of the key to revoke

        Returns:
            True if revoked successfully
        """
        # Find the key
        key = self._get_key_by_id(api_key_id)

        if not key:
            raise ValueError(f"API key {api_key_id} not found")

        if key["user_email"] != user_email:
            raise PermissionError("You can only revoke your own API keys")

        # Update status to revoked
        try:
            self.table.update_item(
                Key={"api_key_hash": key["api_key_hash"]},
                UpdateExpression="SET #status = :status",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues={":status": "revoked"},
            )

            logger.info(f"Revoked API key {api_key_id} for user {user_email}")

            # Audit log
            self._audit_log(
                user_email=user_email,
                action="api_key_revoked",
                api_key_id=api_key_id,
                details={},
            )

            return True
        except ClientError as e:
            logger.error(f"Failed to revoke API key: {e}")
            raise

    def _get_key_by_id(self, api_key_id: str) -> Optional[Dict]:
        """
        Get API key metadata by ID.

        Args:
            api_key_id: API key ID

        Returns:
            Key metadata dict or None
        """
        try:
            response = self.table.query(
                IndexName="ApiKeyIdIndex",
                KeyConditionExpression="api_key_id = :id",
                ExpressionAttributeValues={":id": api_key_id},
            )

            items = response.get("Items", [])
            return items[0] if items else None
        except ClientError as e:
            logger.error(f"Failed to get API key by ID: {e}")
            return None

    def _update_last_used(self, api_key_hash: str) -> None:
        """
        Update the last_used_at timestamp for an API key.

        Args:
            api_key_hash: Hashed API key
        """
        try:
            self.table.update_item(
                Key={"api_key_hash": api_key_hash},
                UpdateExpression="SET last_used_at = :timestamp",
                ExpressionAttributeValues={":timestamp": int(time.time())},
            )
        except ClientError as e:
            # Non-critical error, just log it
            logger.warning(f"Failed to update last_used_at: {e}")

    def _audit_log(self, user_email: str, action: str, api_key_id: str, details: Dict) -> None:
        """
        Create an audit log entry.

        Args:
            user_email: User's email
            action: Action performed
            api_key_id: API key ID
            details: Additional details
        """
        timestamp = int(time.time())
        event_id = f"{user_email}_{action}_{timestamp}_{secrets.token_hex(4)}"

        try:
            self.audit_table.put_item(
                Item={
                    "event_id": event_id,
                    "timestamp": timestamp,
                    "user_email": user_email,
                    "action": action,
                    "api_key_id": api_key_id,
                    "details": details,
                    "expires_at": timestamp + (90 * 24 * 60 * 60),  # 90 days TTL
                }
            )
        except ClientError as e:
            # Non-critical error, just log it
            logger.warning(f"Failed to create audit log: {e}")

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """
        Hash an API key for secure storage.

        Args:
            api_key: API key to hash

        Returns:
            SHA-256 hash of the key
        """
        return hashlib.sha256(api_key.encode()).hexdigest()


# Global instance
_api_key_service: Optional[APIKeyService] = None


def get_api_key_service() -> APIKeyService:
    """Get or create the API key service instance."""
    global _api_key_service
    if _api_key_service is None:
        _api_key_service = APIKeyService()
    return _api_key_service
