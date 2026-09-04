from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.testimonial import TestimonialQueryDTO
from app.application.use_case.public.testimonial.get_public_testimonials_use_case import (
    GetPublicTestimonialsUseCase,
)
from app.deps.testimonial import get_public_testimonials_use_case
from app.schemas.testimonial_schema import TestimonialListResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicTestimonialController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/testimonials",
            tags=["Public - Testimonials"],
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
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_testimonials(
        self,
        params: TestimonialQueryDTO = Depends(),
        use_case: GetPublicTestimonialsUseCase = Depends(get_public_testimonials_use_case),
    ):
        result = await use_case.execute(params)
        return self.build_response(
            message="Testimonials retrieved successfully.",
            data=result.items,
            meta=self.pagination_meta(result),
        )


controller = PublicTestimonialController()
router = controller.router

