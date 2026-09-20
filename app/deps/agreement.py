from fastapi import Depends

from app.application.use_case.admin.vendors.cancel_agreement_use_case import CancelAgreementUseCase
from app.application.use_case.admin.vendors.list_agreements_use_case import ListAgreementsUseCase
from app.application.use_case.admin.vendors.resend_agreement_use_case import ResendAgreementUseCase
from app.application.use_case.admin.vendors.send_agreement_use_case import SendVendorAgreementUseCase
from app.application.use_case.public.agreements.get_public_agreement_use_case import GetPublicAgreementUseCase
from app.application.use_case.public.agreements.sign_agreement_use_case import SignAgreementUseCase
from app.deps.auth import CurrentUser, require_admin_or_staff
from app.deps.service import get_user_service, get_vendor_agreement_service
from app.services.user_service import UserService
from app.services.vendor_agreement_service import VendorAgreementService


async def get_send_vendor_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> SendVendorAgreementUseCase:
    return SendVendorAgreementUseCase(
        agreement_service=agreement_service,
        user_service=user_service,
        current_user=current_user,
    )


async def get_list_agreements_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ListAgreementsUseCase:
    return ListAgreementsUseCase(
        agreement_service=agreement_service,
        current_user=current_user,
    )


async def get_resend_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> ResendAgreementUseCase:
    return ResendAgreementUseCase(
        agreement_service=agreement_service,
        current_user=current_user,
    )


async def get_cancel_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
    current_user: CurrentUser = Depends(require_admin_or_staff),
) -> CancelAgreementUseCase:
    return CancelAgreementUseCase(
        agreement_service=agreement_service,
        current_user=current_user,
    )


async def get_public_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
) -> GetPublicAgreementUseCase:
    return GetPublicAgreementUseCase(
        agreement_service=agreement_service,
    )


async def get_sign_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
) -> SignAgreementUseCase:
    return SignAgreementUseCase(
        agreement_service=agreement_service,
    )


async def get_my_vendor_agreement_use_case(
    agreement_service: VendorAgreementService = Depends(get_vendor_agreement_service),
):
    from app.application.use_case.vendor.agreements.get_my_agreement_use_case import GetMyVendorAgreementUseCase
    return GetMyVendorAgreementUseCase(agreement_service=agreement_service)


