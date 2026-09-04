from fastapi import Depends

from app.application.use_case.admin.review.approve_review_use_case import AdminApproveReviewUseCase
from app.application.use_case.admin.review.delete_review_use_case import AdminDeleteReviewUseCase
from app.application.use_case.admin.review.get_review_use_case import AdminGetReviewUseCase
from app.application.use_case.admin.review.list_reviews_use_case import AdminListReviewsUseCase
from app.application.use_case.admin.review.reject_review_use_case import AdminRejectReviewUseCase
from app.application.use_case.admin.review.update_review_status_use_case import AdminUpdateReviewStatusUseCase
from app.application.use_case.public.review.get_property_reviews_use_case import GetPublicPropertyReviewsUseCase
from app.application.use_case.user.review.create_review_use_case import CreateReviewUseCase
from app.application.use_case.user.review.delete_review_use_case import DeleteReviewUseCase
from app.application.use_case.user.review.get_review_detail_use_case import GetReviewDetailUseCase
from app.application.use_case.user.review.get_user_reviews_use_case import GetUserReviewsUseCase
from app.application.use_case.user.review.update_review_use_case import UpdateReviewUseCase
from app.application.use_case.vendor.review.list_vendor_reviews_use_case import ListVendorReviewsUseCase
from app.application.use_case.vendor.review.reply_review_use_case import VendorReplyReviewUseCase
from app.deps.auth import CurrentUser, get_current_user, require_admin, require_vendor
from app.deps.service import get_booking_service, get_property_service, get_review_service
from app.services.booking_service import BookingService
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService


# --- User Review Dependencies ---

async def get_create_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    booking_service: BookingService = Depends(get_booking_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CreateReviewUseCase:
    return CreateReviewUseCase(review_service, booking_service, current_user)


async def get_user_reviews_use_case(
    review_service: ReviewService = Depends(get_review_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetUserReviewsUseCase:
    return GetUserReviewsUseCase(review_service, current_user)


async def get_review_detail_use_case(
    review_service: ReviewService = Depends(get_review_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetReviewDetailUseCase:
    return GetReviewDetailUseCase(review_service, current_user)


async def get_update_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> UpdateReviewUseCase:
    return UpdateReviewUseCase(review_service, current_user)


async def get_delete_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DeleteReviewUseCase:
    return DeleteReviewUseCase(review_service, current_user)


# --- Admin Review Dependencies ---

async def get_admin_list_reviews_use_case(
    review_service: ReviewService = Depends(get_review_service),
    property_service: PropertyService = Depends(get_property_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminListReviewsUseCase:
    return AdminListReviewsUseCase(review_service, property_service)


async def get_admin_get_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminGetReviewUseCase:
    return AdminGetReviewUseCase(review_service)


async def get_admin_approve_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminApproveReviewUseCase:
    return AdminApproveReviewUseCase(review_service)


async def get_admin_reject_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminRejectReviewUseCase:
    return AdminRejectReviewUseCase(review_service)


async def get_admin_update_review_status_use_case(
    review_service: ReviewService = Depends(get_review_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminUpdateReviewStatusUseCase:
    return AdminUpdateReviewStatusUseCase(review_service)


async def get_admin_delete_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminDeleteReviewUseCase:
    return AdminDeleteReviewUseCase(review_service)


# --- Vendor Review Dependencies ---

async def get_vendor_list_reviews_use_case(
    review_service: ReviewService = Depends(get_review_service),
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> ListVendorReviewsUseCase:
    return ListVendorReviewsUseCase(review_service, property_service, current_user)


async def get_vendor_reply_review_use_case(
    review_service: ReviewService = Depends(get_review_service),
    property_service: PropertyService = Depends(get_property_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> VendorReplyReviewUseCase:
    return VendorReplyReviewUseCase(review_service, property_service, current_user)


# --- Public Review Dependencies ---

async def get_public_property_reviews_use_case(
    review_service: ReviewService = Depends(get_review_service),
    property_service: PropertyService = Depends(get_property_service),
) -> GetPublicPropertyReviewsUseCase:
    return GetPublicPropertyReviewsUseCase(review_service, property_service)

