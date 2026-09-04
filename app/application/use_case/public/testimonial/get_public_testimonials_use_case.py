from app.application.dto.testimonial import TestimonialQueryDTO
from app.models.testimonial_model import Testimonial
from app.repositories.base_repository import Page
from app.services.testimonial_service import TestimonialService


class GetPublicTestimonialsUseCase:
    def __init__(self, testimonial_service: TestimonialService):
        self.testimonial_service = testimonial_service

    async def execute(self, params: TestimonialQueryDTO) -> Page[Testimonial]:
        return await self.testimonial_service.list_public(
            is_featured=params.is_featured,
            user_role=params.user_role,
            page=params.page,
            page_size=params.page_size,
            sort_order=params.sort_order,
            with_relations={"user": True},
        )

