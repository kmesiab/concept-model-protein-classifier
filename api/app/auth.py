"""
API Key authentication and management.
"""

import hashlib
import secrets
from datetime import datetime, timezone
from typing import Optional


class APIKeyManager:
    """
    Manages API key generation and validation.

    In production, this should use a database (PostgreSQL).
    For now, using in-memory storage for demonstration.
    """

    def __init__(self):
        # In-memory storage: api_key_hash -> {metadata}
        self._keys = {}

    def generate_api_key(self, user_email: str, tier: str = "free") -> str:
        """
        Generate a new API key.

        Args:
            user_email: User's email address
            tier: Subscription tier ('free' or 'premium')

        Returns:
            New API key string
        """
        # Generate a secure random API key
        api_key = f"pk_{secrets.token_urlsafe(32)}"

        # Hash the key for storage
        key_hash = self._hash_key(api_key)

        # Store metadata
        self._keys[key_hash] = {
            "email": user_email,
            "tier": tier,
            "created_at": datetime.now(timezone.utc),
            "is_active": True,
            "daily_limit": 1000 if tier == "free" else 100000,
            "rate_limit_per_minute": 100 if tier == "free" else 1000,
            "max_batch_size": 50 if tier == "free" else 500,
        }

        return api_key

    def validate_api_key(self, api_key: str) -> Optional[dict]:
        """
        Validate an API key and return its metadata.

        Args:
            api_key: API key to validate

        Returns:
            Metadata dict if valid, None if invalid
        """
        if not api_key:
            return None

        key_hash = self._hash_key(api_key)
        metadata = self._keys.get(key_hash)

        if metadata and metadata.get("is_active", False):
            return metadata.copy()

        return None

    def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.

        Args:
            api_key: API key to revoke

        Returns:
            True if revoked, False if not found
        """
        key_hash = self._hash_key(api_key)
        metadata = self._keys.get(key_hash)

        if metadata:
            metadata["is_active"] = False
            return True

        return False

    @staticmethod
    def _hash_key(api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()


# Global API key manager instance
api_key_manager = APIKeyManager()


# Pre-create a demo API key for testing
# Note: In production, use proper key management and avoid printing keys
DEMO_API_KEY = api_key_manager.generate_api_key(user_email="demo@example.com", tier="free")
