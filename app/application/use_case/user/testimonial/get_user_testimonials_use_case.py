from app.application.dto.testimonial import TestimonialQueryDTO
from app.deps.auth import CurrentUser
from app.models.testimonial_model import Testimonial
from app.repositories.base_repository import Page
from app.services.testimonial_service import TestimonialService


class GetUserTestimonialsUseCase:
    def __init__(
        self,
        testimonial_service: TestimonialService,
        current_user: CurrentUser,
    ):
        self.testimonial_service = testimonial_service
        self.current_user = current_user

    async def execute(self, params: TestimonialQueryDTO) -> Page[Testimonial]:
        return await self.testimonial_service.list_by_user(
            user_id=self.current_user.id,
            page=params.page,
            page_size=params.page_size,
            sort_order=params.sort_order,
            with_relations={"user": True},
        )

