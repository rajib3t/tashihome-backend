from typing import Optional

from app.application.use_case.base_use_case import BaseUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from app.services.storage_service import StorageService


class GetPropertyUseCase(PropertySerializerMixin, BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        current_user: CurrentUser,
        review_service: Optional[ReviewService] = None,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.current_user = current_user
        self.review_service = review_service

    async def execute(self, property_id: str) -> Optional[dict]:
        property_data = await self.property_service.get_by_public_id(
            property_id,
            with_relations={
                "city": True,
                "location": True,
                "vendor": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
        )

        if not property_data:
            raise AppException(
                message="Property not found",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        rating_summary = None
        if self.review_service and property_data.id:
            rating_summary = await self.review_service.get_property_rating_summary(property_data.id)

        return await self.serialize_property(property_data, rating_summary=rating_summary)

