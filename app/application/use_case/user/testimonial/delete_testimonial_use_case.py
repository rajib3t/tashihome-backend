from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.testimonial_service import TestimonialService


class DeleteTestimonialUseCase:
    def __init__(
        self,
        testimonial_service: TestimonialService,
        current_user: CurrentUser,
    ):
        self.testimonial_service = testimonial_service
        self.current_user = current_user

    async def execute(self, testimonial_id: str) -> None:
        testimonial = await self.testimonial_service.get_by_public_id(testimonial_id)
        if not testimonial:
            raise AppException(404, "Testimonial not found", error_code="TESTIMONIAL_NOT_FOUND")

        if testimonial.user_id != self.current_user.id and self.current_user.role not in ["admin", "staff"]:
            raise AppException(403, "You can only delete your own testimonials", error_code="FORBIDDEN")

        await self.testimonial_service.delete(testimonial)

