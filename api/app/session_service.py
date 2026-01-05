"""
User session management and JWT token service.

Provides secure session management using:
- JWT tokens for stateless authentication
- DynamoDB for session storage and revocation
- Magic link authentication
- AWS Secrets Manager for JWT key management
"""

import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from jose import JWTError, jwt

logger = logging.getLogger(__name__)


class SessionService:
    """
    Manages user sessions with JWT tokens and DynamoDB storage.

    Sessions use short-lived JWT access tokens and refresh tokens
    stored in DynamoDB for revocation capability.
    
    JWT secret key is fetched from AWS Secrets Manager and cached
    for performance. Supports automatic key rotation.
    """

    # Class-level cache for JWT secret (shared across instances)
    _jwt_secret_cache: Optional[Dict[str, any]] = None
    _jwt_secret_cache_time: Optional[float] = None
    _jwt_secret_cache_ttl: int = 3600  # Cache for 1 hour

    def __init__(
        self,
        sessions_table_name: str = None,
        magic_link_table_name: str = None,
        region_name: str = None,
        jwt_secret_name: str = None,
    ):
        """
        Initialize the session service.

        Args:
            sessions_table_name: DynamoDB table name for sessions
            magic_link_table_name: DynamoDB table name for magic links
            region_name: AWS region
            jwt_secret_name: AWS Secrets Manager secret name for JWT key
        """
        self.sessions_table_name = sessions_table_name or os.getenv(
            "DYNAMODB_SESSIONS_TABLE", "protein-classifier-user-sessions"
        )
        self.magic_link_table_name = magic_link_table_name or os.getenv(
            "DYNAMODB_MAGIC_LINKS_TABLE", "protein-classifier-magic-link-tokens"
        )
        self.jwt_secret_name = jwt_secret_name or os.getenv(
            "JWT_SECRET_NAME", "protein-classifier-jwt-secret-key"
        )
        region = region_name or os.getenv("AWS_REGION", "us-west-2")

        # JWT configuration
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60  # 1 hour
        self.refresh_token_expire_days = 30  # 30 days
        self.magic_link_expire_minutes = 15  # 15 minutes

        # Initialize AWS clients
        self.dynamodb = boto3.resource("dynamodb", region_name=region)
        self.secretsmanager = boto3.client("secretsmanager", region_name=region)
        self.sessions_table = self.dynamodb.Table(self.sessions_table_name)
        self.magic_link_table = self.dynamodb.Table(self.magic_link_table_name)

    def _get_jwt_secret(self) -> str:
        """
        Get JWT secret key from AWS Secrets Manager with caching.
        
        Caches the secret for 1 hour to reduce API calls and improve performance.
        Automatically handles secret rotation by refreshing cache.
        
        Returns:
            JWT secret key string
        """
        current_time = time.time()
        
        # Check if cache is valid
        if (
            self._jwt_secret_cache is not None
            and self._jwt_secret_cache_time is not None
            and (current_time - self._jwt_secret_cache_time) < self._jwt_secret_cache_ttl
        ):
            return self._jwt_secret_cache.get("key", "")
        
        # Fetch from Secrets Manager
        try:
            response = self.secretsmanager.get_secret_value(SecretId=self.jwt_secret_name)
            secret_data = json.loads(response["SecretString"])
            
            # Update cache
            SessionService._jwt_secret_cache = secret_data
            SessionService._jwt_secret_cache_time = current_time
            
            logger.info("JWT secret fetched from AWS Secrets Manager and cached")
            return secret_data.get("key", "")
            
        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "ResourceNotFoundException":
                logger.error(f"JWT secret not found: {self.jwt_secret_name}")
            elif error_code == "AccessDeniedException":
                logger.error(f"Access denied to JWT secret: {self.jwt_secret_name}")
            else:
                logger.error(f"Failed to fetch JWT secret: {e}")
            
            # Fallback for development only (should not happen in production)
            logger.warning("Using fallback JWT secret - THIS IS NOT SECURE FOR PRODUCTION")
            return os.getenv("JWT_SECRET_KEY_FALLBACK", secrets.token_urlsafe(32))

    @property
    def secret_key(self) -> str:
        """Get the current JWT secret key (cached)."""
        return self._get_jwt_secret()

    def create_magic_link_token(self, email: str) -> str:
        """
        Create a magic link token for email authentication.

        Args:
            email: User's email address

        Returns:
            Magic link token
        """
        token = secrets.token_urlsafe(32)
        created_at = int(time.time())
        expires_at = created_at + (self.magic_link_expire_minutes * 60)

        try:
            self.magic_link_table.put_item(
                Item={
                    "token": token,
                    "email": email,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "used": False,
                }
            )

            logger.info(f"Created magic link token for {email}")
            return token
        except ClientError as e:
            logger.error(f"Failed to create magic link token: {e}")
            raise

    def verify_magic_link_token(self, token: str) -> Optional[str]:
        """
        Verify a magic link token and return the associated email.

        Args:
            token: Magic link token

        Returns:
            Email address if valid, None otherwise
        """
        try:
            response = self.magic_link_table.get_item(Key={"token": token})
            item = response.get("Item")

            if not item:
                logger.warning(f"Magic link token not found: {token[:8]}...")
                return None

            # Check if already used
            if item.get("used"):
                logger.warning(f"Magic link token already used: {token[:8]}...")
                return None

            # Check if expired
            expires_at = (
                int(item["expires_at"]) if item.get("expires_at") else 0  # type: ignore[arg-type]
            )
            if int(time.time()) > expires_at:
                logger.warning(f"Magic link token expired: {token[:8]}...")
                return None

            # Mark as used
            self.magic_link_table.update_item(
                Key={"token": token},
                UpdateExpression="SET used = :used",
                ExpressionAttributeValues={":used": True},
            )

            email_value = item.get("email")
            return str(email_value) if email_value else None
        except ClientError as e:
            logger.error(f"Failed to verify magic link token: {e}")
            return None

    def create_session(self, email: str) -> Dict:
        """
        Create a new session for a user.

        Args:
            email: User's email address

        Returns:
            Dict with access_token, refresh_token, token_type, and expires_in (int)
        """
        # Generate session ID
        session_id = f"sess_{secrets.token_urlsafe(16)}"

        # Create access token
        access_token = self._create_access_token(email, session_id)

        # Create refresh token and store in DynamoDB
        refresh_token = secrets.token_urlsafe(32)
        created_at = int(time.time())
        expires_at = created_at + (self.refresh_token_expire_days * 24 * 60 * 60)

        try:
            self.sessions_table.put_item(
                Item={
                    "session_id": session_id,
                    "user_email": email,
                    "refresh_token": refresh_token,
                    "created_at": created_at,
                    "expires_at": expires_at,
                    "is_active": True,
                }
            )

            logger.info(f"Created session {session_id} for {email}")

            # Return typed dict for TokenResponse
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
            }
        except ClientError as e:
            logger.error(f"Failed to create session: {e}")
            raise

    def verify_access_token(self, token: str) -> Optional[Dict[str, str]]:
        """
        Verify and decode an access token.

        Args:
            token: JWT access token

        Returns:
            Decoded token payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])

            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.fromtimestamp(exp, tz=timezone.utc) < datetime.now(timezone.utc):
                return None

            return {
                "email": payload.get("sub"),
                "session_id": payload.get("session_id"),
            }
        except JWTError as e:
            logger.warning(f"Invalid access token: {e}")
            return None

    def refresh_access_token(self, refresh_token: str) -> Optional[Dict]:
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dict with access_token, token_type, and expires_in (int), or None
        """
        try:
            # Query session by refresh token using GSI (efficient)
            response = self.sessions_table.query(
                IndexName="RefreshTokenIndex",
                KeyConditionExpression=Key("refresh_token").eq(refresh_token),
                FilterExpression="is_active = :active",
                ExpressionAttributeValues={":active": True},
            )

            items = response.get("Items", [])
            if not items:
                logger.warning("Invalid or inactive refresh token")
                return None

            session = items[0]

            # Check if expired
            expires_at = (
                int(session["expires_at"])  # type: ignore[arg-type]
                if session.get("expires_at")
                else 0
            )
            if int(time.time()) > expires_at:
                logger.warning("Refresh token expired")
                return None

            # Create new access token
            user_email = str(session.get("user_email", ""))
            session_id = str(session.get("session_id", ""))
            access_token = self._create_access_token(user_email, session_id)

            # Return typed dict for TokenResponse
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
            }
        except ClientError as e:
            logger.error(f"Failed to refresh access token: {e}")
            return None

    def revoke_session(self, session_id: str) -> bool:
        """
        Revoke a session.

        Args:
            session_id: Session ID to revoke

        Returns:
            True if revoked successfully
        """
        try:
            self.sessions_table.update_item(
                Key={"session_id": session_id},
                UpdateExpression="SET is_active = :active",
                ExpressionAttributeValues={":active": False},
            )

            logger.info(f"Revoked session {session_id}")
            return True
        except ClientError as e:
            logger.error(f"Failed to revoke session: {e}")
            return False

    def _create_access_token(self, email: str, session_id: str) -> str:
        """
        Create a JWT access token.

        Args:
            email: User's email address
            session_id: Session ID

        Returns:
            JWT access token
        """
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": email,
            "session_id": session_id,
            "iat": now,
            "exp": expires,
            "type": "access",
        }

        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)


# Global instance
_session_service: Optional[SessionService] = None


def get_session_service() -> SessionService:
    """Get or create the session service instance."""
    global _session_service
    if _session_service is None:
        _session_service = SessionService()
    return _session_service
