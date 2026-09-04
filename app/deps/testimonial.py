from fastapi import Depends

from app.application.use_case.admin.testimonial.approve_testimonial_use_case import AdminApproveTestimonialUseCase
from app.application.use_case.admin.testimonial.delete_testimonial_use_case import AdminDeleteTestimonialUseCase
from app.application.use_case.admin.testimonial.get_testimonial_use_case import AdminGetTestimonialUseCase
from app.application.use_case.admin.testimonial.list_testimonials_use_case import AdminListTestimonialsUseCase
from app.application.use_case.admin.testimonial.reject_testimonial_use_case import AdminRejectTestimonialUseCase
from app.application.use_case.admin.testimonial.toggle_feature_testimonial_use_case import AdminToggleFeatureTestimonialUseCase
from app.application.use_case.admin.testimonial.update_testimonial_status_use_case import AdminUpdateTestimonialStatusUseCase
from app.application.use_case.public.testimonial.get_public_testimonials_use_case import GetPublicTestimonialsUseCase
from app.application.use_case.user.testimonial.create_testimonial_use_case import CreateTestimonialUseCase
from app.application.use_case.user.testimonial.delete_testimonial_use_case import DeleteTestimonialUseCase
from app.application.use_case.user.testimonial.get_testimonial_detail_use_case import GetTestimonialDetailUseCase
from app.application.use_case.user.testimonial.get_user_testimonials_use_case import GetUserTestimonialsUseCase
from app.application.use_case.user.testimonial.update_testimonial_use_case import UpdateTestimonialUseCase
from app.deps.auth import CurrentUser, get_current_user, require_admin, require_admin_or_vendor, require_vendor
from app.deps.service import get_testimonial_service, get_user_service
from app.services.testimonial_service import TestimonialService
from app.services.user_service import UserService


# --- User & Vendor Testimonial Dependencies ---

async def get_create_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> CreateTestimonialUseCase:
    return CreateTestimonialUseCase(testimonial_service, user_service, current_user)


async def get_user_testimonials_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetUserTestimonialsUseCase:
    return GetUserTestimonialsUseCase(testimonial_service, current_user)


async def get_testimonial_detail_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> GetTestimonialDetailUseCase:
    return GetTestimonialDetailUseCase(testimonial_service, current_user)


async def get_update_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> UpdateTestimonialUseCase:
    return UpdateTestimonialUseCase(testimonial_service, current_user)


async def get_delete_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    current_user: CurrentUser = Depends(get_current_user),
) -> DeleteTestimonialUseCase:
    return DeleteTestimonialUseCase(testimonial_service, current_user)


# --- Vendor-specific Testimonial Dependencies (if needed) ---

async def get_vendor_create_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    user_service: UserService = Depends(get_user_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> CreateTestimonialUseCase:
    return CreateTestimonialUseCase(testimonial_service, user_service, current_user)


async def get_vendor_testimonials_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    current_user: CurrentUser = Depends(require_vendor),
) -> GetUserTestimonialsUseCase:
    return GetUserTestimonialsUseCase(testimonial_service, current_user)


# --- Admin Testimonial Dependencies ---

async def get_admin_list_testimonials_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminListTestimonialsUseCase:
    return AdminListTestimonialsUseCase(testimonial_service)


async def get_admin_get_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminGetTestimonialUseCase:
    return AdminGetTestimonialUseCase(testimonial_service)


async def get_admin_approve_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminApproveTestimonialUseCase:
    return AdminApproveTestimonialUseCase(testimonial_service)


async def get_admin_reject_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminRejectTestimonialUseCase:
    return AdminRejectTestimonialUseCase(testimonial_service)


async def get_admin_update_testimonial_status_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminUpdateTestimonialStatusUseCase:
    return AdminUpdateTestimonialStatusUseCase(testimonial_service)


async def get_admin_toggle_feature_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminToggleFeatureTestimonialUseCase:
    return AdminToggleFeatureTestimonialUseCase(testimonial_service)


async def get_admin_delete_testimonial_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
    _: CurrentUser = Depends(require_admin),
) -> AdminDeleteTestimonialUseCase:
    return AdminDeleteTestimonialUseCase(testimonial_service)


# --- Public Testimonial Dependencies ---

async def get_public_testimonials_use_case(
    testimonial_service: TestimonialService = Depends(get_testimonial_service),
) -> GetPublicTestimonialsUseCase:
    return GetPublicTestimonialsUseCase(testimonial_service)

