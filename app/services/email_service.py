import logging
import smtplib
from email.message import EmailMessage
import asyncio
import httpx
from brevo import transactional_emails
from mailgun.client import Client
from typing import Optional, List, Sequence, Union
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class EmailMessageData:
    """Represents a single email to send, used for bulk sends with per-recipient content."""
    to_email: str
    subject: str
    text: str
    html: Optional[str] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None


class BaseEmailService(ABC):
    def __init__(self, from_email: Optional[str], from_name: Optional[str]):
        self.from_email = from_email or "noreply@example.com"
        self.from_name = from_name or "Support"
        self.executor = ThreadPoolExecutor(max_workers=5)

    @abstractmethod
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        pass

    async def send_email(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        """Generic entry point: send any email with a given subject/body, optional cc/bcc."""
        await asyncio.get_running_loop().run_in_executor(
            self.executor,
            self._send_email_sync,
            to_email,
            subject,
            text,
            html,
            cc,
            bcc
        )

    async def send_bulk_email(
        self,
        to_emails: Sequence[str],
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        max_concurrency: int = 5
    ) -> dict:
        """Send the same subject/content to many recipients concurrently.

        cc/bcc, if given, are applied to every message in the batch (e.g. looping
        in a manager on every notification). For per-recipient cc/bcc, use
        send_bulk_email_personalized instead.

        Returns a dict of {email: True} for successes and {email: error_str} for failures.
        Individual failures don't stop the rest of the batch.
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results: dict = {}

        async def _send_one(to_email: str):
            async with semaphore:
                try:
                    await self.send_email(to_email, subject, text, html, cc, bcc)
                    results[to_email] = True
                except Exception as e:
                    results[to_email] = str(e)

        await asyncio.gather(*(_send_one(email) for email in to_emails))
        return results

    async def send_bulk_email_personalized(
        self,
        messages: Sequence[Union["EmailMessageData", dict]],
        max_concurrency: int = 5
    ) -> dict:
        """Send different subject/content per recipient concurrently.

        Accepts a list of EmailMessageData or plain dicts with
        to_email/subject/text/html keys.
        Returns a dict of {email: True} for successes and {email: error_str} for failures.
        """
        semaphore = asyncio.Semaphore(max_concurrency)
        results: dict = {}

        async def _send_one(message: Union["EmailMessageData", dict]):
            if isinstance(message, dict):
                message = EmailMessageData(**message)
            async with semaphore:
                try:
                    await self.send_email(
                        message.to_email, message.subject, message.text,
                        message.html, message.cc, message.bcc
                    )
                    results[message.to_email] = True
                except Exception as e:
                    results[message.to_email] = str(e)

        await asyncio.gather(*(_send_one(m) for m in messages))
        return results

    # --- Convenience wrappers for common transactional emails ---
    # These just build the subject/text/html and delegate to send_email,
    # so adding a new email type doesn't require touching each provider class.

    async def send_welcome_email(self, to_email: str, username: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        subject = "Welcome to Our Platform!"
        text = (
            f"Hi {username},\n\n"
            "Welcome to our platform. We're excited to have you on board!\n\n"
            "Best regards,\nThe Team"
        )
        await self.send_email(to_email, subject, text, cc=cc, bcc=bcc)

    async def send_verification_email(self, to_email: str, username: str, verification_link: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        subject = "Verify your email address"
        text = (
            f"Hi {username},\n\n"
            "Thank you for registering. Please verify your email address by clicking the link below:\n\n"
            f"{verification_link}\n\n"
            "If you did not create an account, please ignore this email.\n\n"
            "Best regards,\nThe Team"
        )
        await self.send_email(to_email, subject, text, cc=cc, bcc=bcc)

    async def send_password_reset_email(self, to_email: str, reset_link: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        subject = "Reset Your Password"
        text = (
            f"We received a request to reset your password.\n\n"
            f"Reset it here: {reset_link}\n\n"
            "If you didn't request this, you can safely ignore this email."
        )
        await self.send_email(to_email, subject, text, cc=cc, bcc=bcc)

    async def send_notification_email(self, to_email: str, subject: str, message: str, cc: Optional[List[str]] = None, bcc: Optional[List[str]] = None):
        await self.send_email(to_email, subject, message, cc=cc, bcc=bcc)


class MockEmailService(BaseEmailService):
    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        extra = ""
        if cc:
            extra += f" | Cc: {', '.join(cc)}"
        if bcc:
            extra += f" | Bcc: {', '.join(bcc)}"
        print(f"MOCK EMAIL: To {to_email}{extra} | Subject: {subject}\n{text}")


class SMTPEmailService(BaseEmailService):
    def __init__(self, host: str, port: int, username: Optional[str], password: Optional[str], from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.host = host
        self.port = port
        self.smtp_username = username
        self.smtp_password = password

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = f"{self.from_name} <{self.from_email}>"
        msg["To"] = to_email
        if cc:
            msg["Cc"] = ", ".join(cc)
        if bcc:
            # send_message() reads recipients from To/Cc/Bcc headers, then strips
            # Bcc before actually transmitting the message, so this stays blind.
            msg["Bcc"] = ", ".join(bcc)
        if html:
            msg.set_content("Please enable HTML to view this message.")
            msg.add_alternative(html, subtype='html')
        else:
            msg.set_content(text)

        try:
            with smtplib.SMTP(self.host, self.port) as server:
                try:
                    server.starttls()
                except smtplib.SMTPNotSupportedError:
                    pass  # Local dev servers (e.g. MailHog) don't support STARTTLS
                if self.smtp_username and self.smtp_password:
                    server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            logger.info("SMTP email sent to %s", to_email)
        except Exception as e:
            logger.error("SMTP failed to send email to %s: %s", to_email, e, exc_info=True)
            raise


class MailgunEmailService(BaseEmailService):
    def __init__(self, domain: str, api_key: str, from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.domain = domain
        self.client = Client(auth=("api", api_key))

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        data = {
            "from": f"{self.from_name} <{self.from_email}>",
            "to": to_email,
            "subject": subject,
            "text": text
        }
        if html:
            data["html"] = html
        if cc:
            data["cc"] = ", ".join(cc)
        if bcc:
            data["bcc"] = ", ".join(bcc)

        try:
            self.client.messages.create(data=data, domain=self.domain)
            logger.info("Mailgun email sent to %s", to_email)
        except Exception as e:
            logger.error("Mailgun failed to send email to %s: %s", to_email, e, exc_info=True)
            raise


class BrevoEmailService(BaseEmailService):
    BREVO_API_URL = "https://api.brevo.com/v3/smtp/email"

    def __init__(self, api_key: str, from_email: Optional[str], from_name: Optional[str]):
        super().__init__(from_email, from_name)
        self.api_key = api_key

    def _send_email_sync(
        self,
        to_email: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ):
        payload = transactional_emails.SendTransacEmailRequestToItem(email=to_email)
        sender = transactional_emails.SendTransacEmailRequestSender(
            name=self.from_name, email=self.from_email
        )
        body = {
            "sender": sender.model_dump(),
            "to": [payload.model_dump()],
            "subject": subject,
            "textContent": text
        }
        if html:
            body["htmlContent"] = html
        if cc:
            body["cc"] = [{"email": addr} for addr in cc]
        if bcc:
            body["bcc"] = [{"email": addr} for addr in bcc]

        try:
            with httpx.Client() as client:
                response = client.post(
                    self.BREVO_API_URL,
                    json=body,
                    headers={"api-key": self.api_key, "Content-Type": "application/json"}
                )
                response.raise_for_status()
                print(f"Brevo success dispatch to {to_email}")
        except Exception as e:
            print(f"Brevo error to {to_email}: {e}")