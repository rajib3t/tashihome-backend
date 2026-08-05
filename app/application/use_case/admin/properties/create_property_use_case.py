from app.application.use_case.base_use_case import BaseUseCase
from app.models.property_model import Property
from app.services.property_service import PropertyService
from app.deps.auth import CurrentUser
from app.models.user_model import User
from app.application.dto.properties.property import PropertyDTO
from typing import Optional
from app.core.exceptions import AppException
from app.utils.slug import generate_slug  # adjust import path to wherever this actually lives


class CreatePropertyUseCase(BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        current_user: CurrentUser
    ):
        self.property_service = property_service
        self.current_user = current_user

    async def execute(self, property_dto: PropertyDTO) -> Optional[User]:

        duplicate_name = await self.property_service.get_by_vendor_and_name(
            property_dto.vendor_id, property_dto.name, flush=True
        )
        if duplicate_name:
            raise AppException(
                status_code=409,
                message="A property with this name already exists for this vendor.",
                field="name",
                error_code="PROPERTY_NAME_EXIST",
            )

        base_slug = generate_slug(property_dto.name)
        if not base_slug:
            raise AppException(
                status_code=422,
                message="Slug generation failed.",
                field="slug",
                error_code="SLUG_GENERATION_FAILED",
            )

        property_dto.slug = await self._generate_unique_slug(
            property_dto.vendor_id, base_slug
        )

        payload = Property(
            name=property_dto.name,
            slug=property_dto.slug,
            vendor_id=property_dto.vendor_id,
            location_id=property_dto.location_id,
            description=property_dto.description,
            city_id=property_dto.city_id,
            is_featured=property_dto.is_featured,
            created_by=self.current_user.user_id,
            updated_by=self.current_user.user_id,

        )

        return self.property_service.create(payload)

    async def _generate_unique_slug(self, vendor_id, base_slug: str) -> str:
        """
        WordPress-style slug uniqueness: if 'base_slug' is taken,
        try 'base_slug-2', 'base_slug-3', ... until a free one is found.
        """
        slug = base_slug
        suffix = 2

        while True:
            existing = await self.property_service.get_by_vendor_and_slug(
                vendor_id, slug, flush=True
            )
            if not existing:
                return slug

            slug = f"{base_slug}-{suffix}"
            suffix += 1