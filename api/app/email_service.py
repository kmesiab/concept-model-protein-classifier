"""
Email service for sending magic link authentication emails.

Provides email delivery for:
- Magic link authentication
- API key notifications
- Security alerts

Uses AWS SES in production and console logging in development.
"""

import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for magic link authentication and notifications.

    In development, logs emails to console.
    In production, uses AWS SES.
    """

    def __init__(self):
        """Initialize the email service."""
        self.from_email = os.getenv("SES_FROM_EMAIL", "noreply@proteinclassifier.com")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        self.aws_region = os.getenv("AWS_REGION", "us-west-2")
        self.configuration_set = os.getenv("SES_CONFIGURATION_SET", "protein-classifier-email")

        # Email templates directory
        self.templates_dir = Path(__file__).parent.parent / "email_templates"

        # Template cache for performance
        self._template_cache: Dict[str, str] = {}

        # Check if AWS SES is available (production mode)
        self.ses_enabled = (
            os.getenv("AWS_EXECUTION_ENV") is not None or os.getenv("USE_SES") == "true"
        )

        if self.ses_enabled:
            try:
                import boto3

                self.ses_client = boto3.client("ses", region_name=self.aws_region)
                logger.info("AWS SES client initialized for production email delivery")
            except Exception as e:
                logger.warning(
                    f"Failed to initialize SES client: {e}. Falling back to console logging."
                )
                self.ses_enabled = False
        else:
            logger.warning(
                "AWS SES not enabled. Emails will be logged to console (development mode)"
            )

    async def send_magic_link(self, email: str, token: str) -> bool:
        """
        Send a magic link authentication email.

        Args:
            email: Recipient email address
            token: Magic link token

        Returns:
            True if sent successfully
        """
        magic_link = f"{self.base_url}/api/v1/auth/verify?token={token}"

        subject = "Sign in to Protein Classifier API"

        # Load HTML template
        template_path = self.templates_dir / "magic_link.html"
        html_body = self._load_template(template_path, {"magic_link": magic_link})

        # Plain text fallback
        text_body = f"""
Hello,

Click the link below to sign in to your Protein Classifier API account:

{magic_link}

This link will expire in 15 minutes.

If you didn't request this email, you can safely ignore it.

Best regards,
Protein Classifier API Team
        """.strip()

        return await self._send_email(email, subject, text_body, html_body)

    async def send_api_key_created_notification(
        self, email: str, api_key_id: str, label: str
    ) -> bool:
        """
        Send notification when a new API key is created.

        Args:
            email: User's email address
            api_key_id: ID of the created API key
            label: Label of the API key

        Returns:
            True if sent successfully
        """
        created_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = "New API Key Created - Protein Classifier API"

        # Load HTML template
        template_path = self.templates_dir / "api_key_created.html"
        html_body = self._load_template(
            template_path, {"label": label, "api_key_id": api_key_id, "created_at": created_at}
        )

        # Plain text fallback
        text_body = f"""
Hello,

A new API key has been created for your account:

Label: {label}
Key ID: {api_key_id}
Created: {created_at}

If you didn't create this key, please revoke it immediately and secure your account.

Best regards,
Protein Classifier API Team
        """.strip()

        return await self._send_email(email, subject, text_body, html_body)

    async def send_api_key_revoked_notification(
        self, email: str, api_key_id: str, label: str
    ) -> bool:
        """
        Send notification when an API key is revoked.

        Args:
            email: User's email address
            api_key_id: ID of the revoked API key
            label: Label of the API key

        Returns:
            True if sent successfully
        """
        revoked_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        subject = "API Key Revoked - Protein Classifier API"

        # Load HTML template
        template_path = self.templates_dir / "api_key_revoked.html"
        html_body = self._load_template(
            template_path, {"label": label, "api_key_id": api_key_id, "revoked_at": revoked_at}
        )

        # Plain text fallback
        text_body = f"""
Hello,

An API key has been revoked for your account:

Label: {label}
Key ID: {api_key_id}
Revoked: {revoked_at}

If you didn't revoke this key, please secure your account immediately.

Best regards,
Protein Classifier API Team
        """.strip()

        return await self._send_email(email, subject, text_body, html_body)

    def _load_template(self, template_path: Path, context: dict) -> str:
        """
        Load and render an HTML email template.
        Templates are cached after first load for performance.

        Args:
            template_path: Path to the template file
            context: Dictionary of template variables

        Returns:
            Rendered HTML content
        """
        try:
            # Check cache first
            cache_key = str(template_path)
            if cache_key not in self._template_cache:
                with open(template_path, "r", encoding="utf-8") as f:
                    self._template_cache[cache_key] = f.read()

            template = self._template_cache[cache_key]

            # Simple template variable replacement
            for key, value in context.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))

            return template
        except Exception as e:
            logger.error(f"Failed to load template {template_path}: {e}")
            return ""

    async def _send_email(
        self, to_email: str, subject: str, text_body: str, html_body: Optional[str] = None
    ) -> bool:
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            text_body: Email body (plain text)
            html_body: Email body (HTML, optional)

        Returns:
            True if sent successfully
        """
        # Development mode: log to console
        if not self.ses_enabled:
            logger.info("=" * 80)
            logger.info(f"EMAIL TO: {to_email}")
            logger.info(f"FROM: {self.from_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info("-" * 80)
            logger.info(text_body)
            if html_body:
                logger.info("-" * 80)
                logger.info("HTML version available")
            logger.info("=" * 80)
            return True

        # Production mode: send via AWS SES
        try:
            message: dict = {
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {"Text": {"Data": text_body, "Charset": "UTF-8"}},
            }

            # Add HTML body if provided
            if html_body:
                message["Body"]["Html"] = {"Data": html_body, "Charset": "UTF-8"}

            response = self.ses_client.send_email(
                Source=self.from_email,
                Destination={"ToAddresses": [to_email]},
                Message=message,
                ConfigurationSetName=self.configuration_set,
            )

            logger.info(f"Email sent to {to_email}, MessageId: {response['MessageId']}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email via SES: {e}")
            return False


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
