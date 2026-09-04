from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.testimonial_model import Testimonial
from app.services.testimonial_service import TestimonialService


class GetTestimonialDetailUseCase:
    def __init__(
        self,
        testimonial_service: TestimonialService,
        current_user: CurrentUser,
    ):
        self.testimonial_service = testimonial_service
        self.current_user = current_user

    async def execute(self, testimonial_id: str) -> Testimonial:
        testimonial = await self.testimonial_service.get_by_public_id(
            testimonial_id,
            with_relations={"user": True},
        )
        if not testimonial:
            raise AppException(404, "Testimonial not found", error_code="TESTIMONIAL_NOT_FOUND")

        if testimonial.user_id != self.current_user.id and self.current_user.role not in ["admin", "staff"]:
            raise AppException(403, "Access denied", error_code="FORBIDDEN")

        return testimonial

