from datetime import datetime, timezone
from typing import Optional

from app.application.dto.payouts.payout import AdminPayoutProcessDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.config import settings
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.payout_model import Payout, PayoutStatus
from app.models.vendor_bank_account_model import BankAccountType, VendorBankAccount
from app.services.payout_service import PayoutService
from app.services.razorpay_service import RazorpayService
from app.services.user_service import UserService
from app.services.vendor_bank_account_service import VendorBankAccountService

_RELATIONS = {
    "vendor": True,
    "bank_account": True,
    "creator": True,
}


class ProcessRazorpayPayoutUseCase(BaseUseCase):
    def __init__(
        self,
        payout_service: PayoutService,
        user_service: UserService,
        vendor_bank_account_service: VendorBankAccountService,
        razorpay_service: RazorpayService,
        current_user: CurrentUser,
    ):
        self.payout_service = payout_service
        self.user_service = user_service
        self.vendor_bank_account_service = vendor_bank_account_service
        self.razorpay_service = razorpay_service
        self.current_user = current_user

    async def execute(self, payout_id: str, data: Optional[AdminPayoutProcessDTO] = None) -> Payout:
        if not settings.PAYMENT_ENABLED:
            raise AppException(
                status_code=400,
                message="Payment and payout processing is currently disabled.",
                error_code="PAYMENT_DISABLED",
            )

        payout = await self.payout_service.get_by_public_id(
            payout_id,
            with_relations=_RELATIONS,
        )
        if not payout:
            raise AppException(
                status_code=404,
                message="Payout record not found.",
                error_code="PAYOUT_NOT_FOUND",
                field="payout_id",
            )

        if payout.status in [PayoutStatus.PAID, PayoutStatus.PROCESSING]:
            raise AppException(
                status_code=400,
                message=f"Payout is already in '{payout.status.value}' state and cannot be re-processed.",
                error_code="PAYOUT_ALREADY_PROCESSED",
            )

        # Ensure vendor and bank account are available
        vendor = payout.vendor or await self.user_service.get_user_by_id(payout.vendor_id)
        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor associated with this payout was not found.",
                error_code="VENDOR_NOT_FOUND",
            )

        bank_account = payout.bank_account
        if not bank_account:
            bank_account = await self.vendor_bank_account_service.get_primary_by_vendor_id(vendor.id)
            if not bank_account:
                raise AppException(
                    status_code=400,
                    message="No bank account or UPI VPA found for vendor. Please configure payout destination first.",
                    error_code="VENDOR_BANK_ACCOUNT_MISSING",
                )
            payout.bank_account_id = bank_account.id

        # Ensure Razorpay Contact & Fund Account exist
        fund_account_id = bank_account.razorpay_fund_account_id
        if not fund_account_id:
            fund_account_id = await self._ensure_razorpay_fund_account(vendor, bank_account)

        # Determine payout mode
        payout_mode = (data.mode if data and data.mode else payout.mode) or "NEFT"
        narration = (data.narration if data and data.narration else "Homestay Payout")
        notes = data.notes if data and data.notes else {"payout_id": str(payout.public_id)}

        try:
            rzp_response = await self.razorpay_service.create_payout(
                fund_account_id=fund_account_id,
                amount=float(payout.amount),
                currency=payout.currency or "INR",
                mode=payout_mode,
                purpose="payout",
                reference_id=str(payout.public_id),
                narration=narration,
                notes=notes,
            )

            payout.razorpay_payout_id = rzp_response.get("id")
            payout.razorpay_fund_account_id = fund_account_id
            payout.transaction_id = rzp_response.get("id")
            payout.utr = rzp_response.get("utr")
            payout.mode = payout_mode

            rzp_status = rzp_response.get("status", "").lower()
            if rzp_status in ["processed", "paid"]:
                payout.status = PayoutStatus.PAID
                payout.paid_at = datetime.now(timezone.utc)
            elif rzp_status in ["queued", "processing", "pending"]:
                payout.status = PayoutStatus.PROCESSING
            elif rzp_status in ["rejected"]:
                payout.status = PayoutStatus.REJECTED
                payout.failure_reason = rzp_response.get("failure_reason")
            elif rzp_status in ["reversed"]:
                payout.status = PayoutStatus.REVERSED
                payout.failure_reason = rzp_response.get("failure_reason")
            else:
                payout.status = PayoutStatus.PROCESSING

        except AppException as e:
            payout.status = PayoutStatus.FAILED
            payout.failure_reason = e.message
            await self.payout_service.update(payout, with_relations=_RELATIONS)
            raise e

        return await self.payout_service.update(payout, with_relations=_RELATIONS)

    async def _ensure_razorpay_fund_account(self, vendor, bank_account: VendorBankAccount) -> str:
        """Helper to create contact & fund account on RazorpayX if not already created."""
        contact_id = bank_account.razorpay_contact_id
        if not contact_id:
            contact_res = await self.razorpay_service.create_contact(
                name=vendor.full_name or "Vendor",
                email=vendor.email,
                contact=vendor.phone,
                type="vendor",
                reference_id=str(vendor.public_id),
            )
            contact_id = contact_res.get("id")
            bank_account.razorpay_contact_id = contact_id

        if bank_account.account_type == BankAccountType.VPA and bank_account.upi_id:
            fa_res = await self.razorpay_service.create_fund_account_vpa(
                contact_id=contact_id,
                vpa_address=bank_account.upi_id,
            )
        else:
            if not bank_account.account_number or not bank_account.ifsc_code:
                raise AppException(
                    status_code=400,
                    message="Bank account number and IFSC code are required to process bank payout.",
                    error_code="INVALID_BANK_DETAILS",
                )
            fa_res = await self.razorpay_service.create_fund_account_bank(
                contact_id=contact_id,
                account_holder_name=bank_account.account_holder_name,
                account_number=bank_account.account_number,
                ifsc=bank_account.ifsc_code,
            )

        fund_account_id = fa_res.get("id")
        bank_account.razorpay_fund_account_id = fund_account_id
        bank_account.is_verified = True
        await self.vendor_bank_account_service.update(bank_account)
        return fund_account_id

