"""
Email service for sending magic link authentication emails.

Provides email delivery for:
- Magic link authentication
- API key notifications
- Security alerts
"""

import logging
import os
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for magic link authentication and notifications.

    In development, logs emails to console.
    In production, uses configured SMTP server.
    """

    def __init__(self):
        """Initialize the email service."""
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@protein-classifier.com")
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")

        # Check if SMTP is configured
        self.smtp_configured = all([self.smtp_host, self.smtp_username, self.smtp_password])

        if not self.smtp_configured:
            logger.warning(
                "SMTP not configured. Emails will be logged to console (development mode)"
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
        body = f"""
        Hello,

        Click the link below to sign in to your Protein Classifier API account:

        {magic_link}

        This link will expire in 15 minutes.

        If you didn't request this email, you can safely ignore it.

        Best regards,
        Protein Classifier API Team
        """

        return await self._send_email(email, subject, body)

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
        subject = "New API Key Created - Protein Classifier API"
        body = f"""
        Hello,

        A new API key has been created for your account:

        Label: {label}
        Key ID: {api_key_id}
        Created: Now

        If you didn't create this key, please revoke it immediately and secure your account.

        Best regards,
        Protein Classifier API Team
        """

        return await self._send_email(email, subject, body)

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
        subject = "API Key Revoked - Protein Classifier API"
        body = f"""
        Hello,

        An API key has been revoked for your account:

        Label: {label}
        Key ID: {api_key_id}

        If you didn't revoke this key, please secure your account immediately.

        Best regards,
        Protein Classifier API Team
        """

        return await self._send_email(email, subject, body)

    async def _send_email(
        self, to_email: str, subject: str, body: str
    ) -> bool:  # pylint: disable=too-many-return-statements
        """
        Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text)

        Returns:
            True if sent successfully
        """
        # Development mode: log to console
        if not self.smtp_configured:
            logger.info("=" * 80)
            logger.info(f"EMAIL TO: {to_email}")
            logger.info(f"SUBJECT: {subject}")
            logger.info("-" * 80)
            logger.info(body)
            logger.info("=" * 80)
            return True

        # Production mode: send via SMTP
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText

            import aiosmtplib

            message = MIMEMultipart()
            message["From"] = self.from_email
            message["To"] = to_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_username,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"Email sent to {to_email}")
            return True
        except Exception as e:
            logger.error(f"Failed to send email: {e}")
            return False


# Global instance
_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Get or create the email service instance."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
