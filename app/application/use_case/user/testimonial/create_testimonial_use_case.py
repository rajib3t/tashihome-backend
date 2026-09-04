from app.application.dto.testimonial import TestimonialCreateDTO
from app.deps.auth import CurrentUser
from app.models.testimonial_model import Testimonial, TestimonialStatus
from app.services.testimonial_service import TestimonialService
from app.services.user_service import UserService


class CreateTestimonialUseCase:
    def __init__(
        self,
        testimonial_service: TestimonialService,
        user_service: UserService,
        current_user: CurrentUser,
    ):
        self.testimonial_service = testimonial_service
        self.user_service = user_service
        self.current_user = current_user

    async def execute(self, dto: TestimonialCreateDTO) -> Testimonial:
        user = await self.user_service.get_user_by_id(self.current_user.id)

        author_name = dto.name or (user.full_name if user and user.full_name else "Anonymous User")
        avatar_url = dto.avatar_url or (user.is_profile_image_url if user else None)
        designation = dto.designation or ("Host" if self.current_user.role == "vendor" else "Guest")

        testimonial = Testimonial(
            user_id=self.current_user.id,
            user_role=self.current_user.role,
            name=author_name,
            designation=designation,
            avatar_url=avatar_url,
            rating=dto.rating,
            content=dto.content,
            status=TestimonialStatus.PENDING,
            is_featured=False,
        )

        return await self.testimonial_service.create(
            testimonial,
            with_relations={"user": True},
        )

