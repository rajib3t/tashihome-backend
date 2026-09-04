from app.application.dto.testimonial import TestimonialStatusUpdateDTO
from app.core.exceptions import AppException
from app.models.testimonial_model import Testimonial, TestimonialStatus
from app.services.testimonial_service import TestimonialService


class AdminUpdateTestimonialStatusUseCase:
    def __init__(self, testimonial_service: TestimonialService):
        self.testimonial_service = testimonial_service

    async def execute(self, testimonial_id: str, dto: TestimonialStatusUpdateDTO) -> Testimonial:
        testimonial = await self.testimonial_service.get_by_public_id(
            testimonial_id,
            with_relations={"user": True},
        )
        if not testimonial:
            raise AppException(404, "Testimonial not found", error_code="TESTIMONIAL_NOT_FOUND")

        try:
            testimonial.status = TestimonialStatus(dto.status.lower())
        except ValueError:
            try:
                testimonial.status = TestimonialStatus[dto.status.upper()]
            except KeyError:
                raise AppException(400, f"Invalid status '{dto.status}'", error_code="INVALID_STATUS")

        return await self.testimonial_service.update(
            testimonial,
            with_relations={"user": True},
        )

