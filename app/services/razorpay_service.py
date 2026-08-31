import hashlib
import hmac
import logging
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


class RazorpayService:
    BASE_URL = "https://api.razorpay.com/v1"

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
        account_number: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET
        self.account_number = account_number or settings.RAZORPAYX_ACCOUNT_NUMBER

    def is_configured(self) -> bool:
        return bool(self.key_id and self.key_secret)

    def _get_auth(self) -> tuple[str, str]:
        if not self.is_configured():
            raise AppException(
                status_code=500,
                message="Razorpay credentials are not configured.",
                error_code="RAZORPAY_NOT_CONFIGURED",
            )
        return (self.key_id, self.key_secret)

    async def create_order(
        self,
        amount: float,
        currency: str = "INR",
        receipt: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a Razorpay order.
        Amount is converted to the smallest currency unit (paise for INR).
        """
        auth = self._get_auth()
        amount_in_paise = int(round(amount * 100))

        payload: Dict[str, Any] = {
            "amount": amount_in_paise,
            "currency": currency,
            "payment_capture": 1,
        }
        if receipt:
            payload["receipt"] = receipt[:40]
        if notes:
            payload["notes"] = {k: str(v) for k, v in notes.items()}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/orders",
                    json=payload,
                    auth=auth,
                )
                if response.status_code != 200:
                    logger.error(
                        "Razorpay order creation failed: %s - %s",
                        response.status_code,
                        response.text,
                    )
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to create Razorpay payment order.",
                        error_code="RAZORPAY_ORDER_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while calling Razorpay: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    def verify_payment_signature(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
    ) -> bool:
        """
        Verifies the signature returned by Razorpay Checkout.
        """
        if not self.key_secret:
            raise AppException(
                status_code=500,
                message="Razorpay key secret is not configured.",
                error_code="RAZORPAY_NOT_CONFIGURED",
            )

        payload = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, razorpay_signature)

    def verify_webhook_signature(self, body: bytes | str, signature: str) -> bool:
        """
        Verifies the webhook payload signature.
        """
        if not self.webhook_secret:
            logger.warning("Razorpay webhook secret is not configured.")
            return False

        if isinstance(body, str):
            body = body.encode("utf-8")

        expected_signature = hmac.new(
            self.webhook_secret.encode("utf-8"),
            body,
            hashlib.sha256,
        ).hexdigest()

        return hmac.compare_digest(expected_signature, signature)

    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """
        Fetches payment details from Razorpay by payment ID.
        """
        auth = self._get_auth()
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/payments/{payment_id}",
                    auth=auth,
                )
                if response.status_code != 200:
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to fetch Razorpay payment.",
                        error_code="RAZORPAY_PAYMENT_FETCH_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while calling Razorpay fetch payment: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def create_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Initiates a refund via Razorpay.
        """
        auth = self._get_auth()
        payload: Dict[str, Any] = {}
        if amount is not None and amount > 0:
            payload["amount"] = int(round(amount * 100))
        if notes:
            payload["notes"] = {k: str(v) for k, v in notes.items()}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/payments/{payment_id}/refund",
                    json=payload,
                    auth=auth,
                )
                if response.status_code != 200:
                    logger.error("Razorpay refund failed: %s - %s", response.status_code, response.text)
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to process refund via Razorpay.",
                        error_code="RAZORPAY_REFUND_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while calling Razorpay refund: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    # -------------------------------------------------------------------------
    # RazorpayX Payouts & Fund Account APIs
    # -------------------------------------------------------------------------

    async def create_contact(
        self,
        name: str,
        email: Optional[str] = None,
        contact: Optional[str] = None,
        type: str = "vendor",
        reference_id: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a contact in RazorpayX for a vendor.
        """
        auth = self._get_auth()
        payload: Dict[str, Any] = {
            "name": name,
            "type": type,
        }
        if email:
            payload["email"] = email
        if contact:
            payload["contact"] = contact
        if reference_id:
            payload["reference_id"] = str(reference_id)
        if notes:
            payload["notes"] = {k: str(v) for k, v in notes.items()}

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/contacts",
                    json=payload,
                    auth=auth,
                )
                if response.status_code not in (200, 201):
                    logger.error("RazorpayX contact creation failed: %s - %s", response.status_code, response.text)
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to create RazorpayX contact for vendor.",
                        error_code="RAZORPAY_CONTACT_CREATION_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while creating Razorpay contact: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def create_fund_account_bank(
        self,
        contact_id: str,
        account_holder_name: str,
        account_number: str,
        ifsc: str,
    ) -> Dict[str, Any]:
        """
        Creates a bank fund account linked to a contact in RazorpayX.
        """
        auth = self._get_auth()
        payload = {
            "contact_id": contact_id,
            "account_type": "bank_account",
            "bank_account": {
                "name": account_holder_name,
                "ifsc": ifsc.upper(),
                "account_number": account_number,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/fund_accounts",
                    json=payload,
                    auth=auth,
                )
                if response.status_code not in (200, 201):
                    logger.error("RazorpayX fund account creation failed: %s - %s", response.status_code, response.text)
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to create RazorpayX fund account for vendor.",
                        error_code="RAZORPAY_FUND_ACCOUNT_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while creating Razorpay fund account: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def create_fund_account_vpa(
        self,
        contact_id: str,
        vpa_address: str,
    ) -> Dict[str, Any]:
        """
        Creates a UPI VPA fund account linked to a contact in RazorpayX.
        """
        auth = self._get_auth()
        payload = {
            "contact_id": contact_id,
            "account_type": "vpa",
            "vpa": {
                "address": vpa_address,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/fund_accounts",
                    json=payload,
                    auth=auth,
                )
                if response.status_code not in (200, 201):
                    logger.error("RazorpayX VPA fund account creation failed: %s - %s", response.status_code, response.text)
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to create RazorpayX UPI fund account for vendor.",
                        error_code="RAZORPAY_FUND_ACCOUNT_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while creating Razorpay VPA fund account: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def create_payout(
        self,
        fund_account_id: str,
        amount: float,
        currency: str = "INR",
        mode: str = "NEFT",
        purpose: str = "payout",
        account_number: Optional[str] = None,
        queue_if_low_balance: bool = True,
        reference_id: Optional[str] = None,
        narration: Optional[str] = "Homestay Payout",
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes a direct payout via RazorpayX.
        Amount is converted to the smallest currency unit (paise for INR).
        """
        auth = self._get_auth()
        source_account = account_number or self.account_number
        if not source_account:
            raise AppException(
                status_code=500,
                message="RazorpayX source account number is not configured.",
                error_code="RAZORPAYX_ACCOUNT_NOT_CONFIGURED",
            )

        amount_in_paise = int(round(amount * 100))
        payload: Dict[str, Any] = {
            "account_number": source_account,
            "fund_account_id": fund_account_id,
            "amount": amount_in_paise,
            "currency": currency,
            "mode": mode.upper(),
            "purpose": purpose,
            "queue_if_low_balance": queue_if_low_balance,
        }
        if reference_id:
            payload["reference_id"] = str(reference_id)
        if narration:
            payload["narration"] = narration[:30]
        if notes:
            payload["notes"] = {k: str(v) for k, v in notes.items()}

        async with httpx.AsyncClient(timeout=20.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/payouts",
                    json=payload,
                    auth=auth,
                )
                if response.status_code not in (200, 201):
                    logger.error("RazorpayX payout failed: %s - %s", response.status_code, response.text)
                    raise AppException(
                        status_code=response.status_code,
                        message=f"RazorpayX payout failed: {response.text}",
                        error_code="RAZORPAY_PAYOUT_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while executing Razorpay payout: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def fetch_payout(self, payout_id: str) -> Dict[str, Any]:
        """
        Fetches payout details and live status from RazorpayX.
        """
        auth = self._get_auth()
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.get(
                    f"{self.BASE_URL}/payouts/{payout_id}",
                    auth=auth,
                )
                if response.status_code != 200:
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to fetch Razorpay payout details.",
                        error_code="RAZORPAY_PAYOUT_FETCH_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while fetching Razorpay payout: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )

    async def cancel_payout(self, payout_id: str) -> Dict[str, Any]:
        """
        Cancels a queued payout in RazorpayX.
        """
        auth = self._get_auth()
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.BASE_URL}/payouts/{payout_id}/cancel",
                    auth=auth,
                )
                if response.status_code != 200:
                    raise AppException(
                        status_code=response.status_code,
                        message="Failed to cancel Razorpay payout.",
                        error_code="RAZORPAY_PAYOUT_CANCEL_FAILED",
                    )
                return response.json()
            except httpx.HTTPError as e:
                logger.error("HTTP error while cancelling Razorpay payout: %s", str(e))
                raise AppException(
                    status_code=502,
                    message="Network error communicating with Razorpay.",
                    error_code="RAZORPAY_NETWORK_ERROR",
                )
