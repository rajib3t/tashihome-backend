from fastapi import APIRouter, Body, Depends

from app.api.base_controller import BaseController
from app.application.dto.testimonial import (
    TestimonialCreateDTO,
    TestimonialQueryDTO,
    TestimonialUpdateDTO,
)
from app.application.use_case.user.testimonial.create_testimonial_use_case import CreateTestimonialUseCase
from app.application.use_case.user.testimonial.delete_testimonial_use_case import DeleteTestimonialUseCase
from app.application.use_case.user.testimonial.get_testimonial_detail_use_case import GetTestimonialDetailUseCase
from app.application.use_case.user.testimonial.get_user_testimonials_use_case import GetUserTestimonialsUseCase
from app.application.use_case.user.testimonial.update_testimonial_use_case import UpdateTestimonialUseCase
from app.core.csrf import verify_csrf
from app.deps.idempotency import require_idempotency_key
from app.deps.testimonial import (
    get_delete_testimonial_use_case,
    get_testimonial_detail_use_case,
    get_update_testimonial_use_case,
    get_vendor_create_testimonial_use_case,
    get_vendor_testimonials_use_case,
)
from app.schemas.testimonial_schema import (
    TestimonialListResponseSchema,
    TestimonialResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class VendorTestimonialController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/testimonials",
            tags=["Vendor - Testimonials"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "post",
                "/",
                self._create_testimonial,
                {
                    "response_model": TestimonialResponseSchema,
                    "status_code": 201,
                    "dependencies": [Depends(verify_csrf), Depends(require_idempotency_key)],
                },
            ),
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
                "put",
                "/{testimonial_id}",
                self._update_testimonial,
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
    async def _create_testimonial(
        self,
        data: TestimonialCreateDTO,
        use_case: CreateTestimonialUseCase = Depends(get_vendor_create_testimonial_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Host testimonial submitted successfully and is pending approval.",
            data=result,
        )

    @handle_api_exceptions
    async def _get_testimonials(
        self,
        params: TestimonialQueryDTO = Depends(),
        use_case: GetUserTestimonialsUseCase = Depends(get_vendor_testimonials_use_case),
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
        use_case: GetTestimonialDetailUseCase = Depends(get_testimonial_detail_use_case),
    ):
        result = await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial retrieved successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _update_testimonial(
        self,
        testimonial_id: str,
        data: TestimonialUpdateDTO = Body(...),
        use_case: UpdateTestimonialUseCase = Depends(get_update_testimonial_use_case),
    ):
        result = await use_case.execute(testimonial_id, data)
        return self.build_response(
            message="Testimonial updated successfully and is pending approval.",
            data=result,
        )

    @handle_api_exceptions
    async def _delete_testimonial(
        self,
        testimonial_id: str,
        use_case: DeleteTestimonialUseCase = Depends(get_delete_testimonial_use_case),
    ):
        await use_case.execute(testimonial_id)
        return self.build_response(
            message="Testimonial deleted successfully.",
            data=None,
        )


controller = VendorTestimonialController()
router = controller.router

