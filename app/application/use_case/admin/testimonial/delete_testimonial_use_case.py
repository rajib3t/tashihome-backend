from app.core.exceptions import AppException
from app.services.testimonial_service import TestimonialService


class AdminDeleteTestimonialUseCase:
    def __init__(self, testimonial_service: TestimonialService):
        self.testimonial_service = testimonial_service

    async def execute(self, testimonial_id: str) -> None:
        testimonial = await self.testimonial_service.get_by_public_id(testimonial_id)
        if not testimonial:
            raise AppException(404, "Testimonial not found", error_code="TESTIMONIAL_NOT_FOUND")

        await self.testimonial_service.delete(testimonial)

