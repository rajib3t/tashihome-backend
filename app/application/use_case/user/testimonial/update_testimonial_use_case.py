from app.application.dto.testimonial import TestimonialUpdateDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.testimonial_model import Testimonial, TestimonialStatus
from app.services.testimonial_service import TestimonialService


class UpdateTestimonialUseCase:
    def __init__(
        self,
        testimonial_service: TestimonialService,
        current_user: CurrentUser,
    ):
        self.testimonial_service = testimonial_service
        self.current_user = current_user

    async def execute(self, testimonial_id: str, dto: TestimonialUpdateDTO) -> Testimonial:
        testimonial = await self.testimonial_service.get_by_public_id(
            testimonial_id,
            with_relations={"user": True},
        )
        if not testimonial:
            raise AppException(404, "Testimonial not found", error_code="TESTIMONIAL_NOT_FOUND")

        if testimonial.user_id != self.current_user.id:
            raise AppException(403, "You can only update your own testimonials", error_code="FORBIDDEN")

        if dto.name is not None:
            testimonial.name = dto.name
        if dto.designation is not None:
            testimonial.designation = dto.designation
        if dto.avatar_url is not None:
            testimonial.avatar_url = dto.avatar_url
        if dto.rating is not None:
            testimonial.rating = dto.rating
        if dto.content is not None:
            testimonial.content = dto.content

        # Update resets status to PENDING
        testimonial.status = TestimonialStatus.PENDING

        return await self.testimonial_service.update(
            testimonial,
            with_relations={"user": True},
        )

