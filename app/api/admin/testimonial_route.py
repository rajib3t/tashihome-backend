from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.testimonial import (
    TestimonialFeatureToggleDTO,
    TestimonialQueryDTO,
    TestimonialStatusUpdateDTO,
)
from app.application.use_case.admin.testimonial.approve_testimonial_use_case import AdminApproveTestimonialUseCase
from app.application.use_case.admin.testimonial.delete_testimonial_use_case import AdminDeleteTestimonialUseCase
from app.application.use_case.admin.testimonial.get_testimonial_use_case import AdminGetTestimonialUseCase
from app.application.use_case.admin.testimonial.list_testimonials_use_case import AdminListTestimonialsUseCase
from app.application.use_case.admin.testimonial.reject_testimonial_use_case import AdminRejectTestimonialUseCase
from app.application.use_case.admin.testimonial.toggle_feature_testimonial_use_case import (
    AdminToggleFeatureTestimonialUseCase,
)
from app.application.use_case.admin.testimonial.update_testimonial_status_use_case import (
    AdminUpdateTestimonialStatusUseCase,
)
from app.core.csrf import verify_csrf
from app.deps.testimonial import (
    get_admin_approve_testimonial_use_case,
    get_admin_delete_testimonial_use_case,
    get_admin_get_testimonial_use_case,
    get_admin_list_testimonials_use_case,
    get_admin_reject_testimonial_use_case,
    get_admin_toggle_feature_testimonial_use_case,
    get_admin_update_testimonial_status_use_case,
)
from app.schemas.testimonial_schema import (
    TestimonialListResponseSchema,
    TestimonialResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class AdminTestimonialController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/testimonials",
            tags=["Admin - Testimonials"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._get_testimonials,
                {"response_model": TestimonialListResponseSchema},
            ),
            (
                "get",
                "/{testimonial_id}",
                self._get_testimonial,
                {"response_model": TestimonialResponseSchema},
            ),
            (
                "post",
                "/{testimonial_id}/approve",
                self._approve_testimonial,
                {
                    "response_model": TestimonialResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "post",
                "/{testimonial_id}/reject",
                self._reject_testimonial,
                {
                    "response_model": TestimonialResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "patch",
                "/{testimonial_id}/status",
                self._update_status,
                {
                    "response_model": TestimonialResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "patch",
                "/{testimonial_id}/feature",
                self._toggle_feature,
                {
                    "response_model": TestimonialResponseSchema,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "delete",
                "/{testimonial_id}",
                self._delete_testimonial,
                {
                    "status_code": 200,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_testimonials(
        self,
        params: TestimonialQueryDTO = Depends(),
        use_case: AdminListTestimonialsUseCase = Depends(get_admin_list_testimonials_use_case),
    ):
        result = await use_case.execute(params)
        return self.build_response(
            message="Testimonials retrieved successfully.",
            data=result.items,
            meta=self.pagination_meta(result),
        )

    @handle_api_exceptions
    async def _get_testimonial(
        self,
        testimonial_id: str,
        use_case: AdminGetTestimonialUseCase = Depends(get_admin_get_testimonial_use_case),
    ):
        result = await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _approve_testimonial(
        self,
        testimonial_id: str,
        use_case: AdminApproveTestimonialUseCase = Depends(get_admin_approve_testimonial_use_case),
    ):
        result = await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial approved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _reject_testimonial(
        self,
        testimonial_id: str,
        use_case: AdminRejectTestimonialUseCase = Depends(get_admin_reject_testimonial_use_case),
    ):
        result = await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial rejected successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _update_status(
        self,
        testimonial_id: str,
        data: TestimonialStatusUpdateDTO = Body(...),
        use_case: AdminUpdateTestimonialStatusUseCase = Depends(get_admin_update_testimonial_status_use_case),
    ):
        result = await use_case.execute(testimonial_id, data)
        return self.build_response(
            message="Testimonial status updated successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _toggle_feature(
        self,
        testimonial_id: str,
        data: TestimonialFeatureToggleDTO = Body(...),
        use_case: AdminToggleFeatureTestimonialUseCase = Depends(get_admin_toggle_feature_testimonial_use_case),
    ):
        result = await use_case.execute(testimonial_id, data)
        return self.build_response(
            message="Testimonial feature status updated successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _delete_testimonial(
        self,
        testimonial_id: str,
        use_case: AdminDeleteTestimonialUseCase = Depends(get_admin_delete_testimonial_use_case),
    ):
        await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial deleted successfully.",
            data=None,
        )


controller = AdminTestimonialController()
router = controller.router

