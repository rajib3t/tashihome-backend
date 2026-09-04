from datetime import date
from typing import Optional

from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.services.booking_service import BookingService
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from app.services.storage_service import StorageService


class PublicGetPropertyUseCase(BaseUseCase, PropertySerializerMixin):
    def __init__(
        self,
        property_service: PropertyService,
        storage_service: StorageService,
        booking_service: Optional[BookingService] = None,
        review_service: Optional[ReviewService] = None,
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.booking_service = booking_service
        self.review_service = review_service

    async def execute(
        self,
        slug: str,
        check_in_date: Optional[date] = None,
        check_out_date: Optional[date] = None,
    ) -> Optional[dict]:
        property_data = await self.property_service.get_by_slug(
            slug,
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

        availability_map = None
        if check_in_date and check_out_date and self.booking_service and property_data.property_room_types:
            availability_map = {}
            for item in property_data.property_room_types:
                total_u = item.total_units or 1
                booked = await self.booking_service.booking_repository.count_booked_units(
                    property_id=property_data.id,
                    room_type_id=item.room_type_id,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                )
                blocked = await self.booking_service.room_block_repository.count_blocked_units(
                    property_id=property_data.id,
                    room_type_id=item.room_type_id,
                    check_in_date=check_in_date,
                    check_out_date=check_out_date,
                )
                avail = max(0, total_u - (booked + blocked))
                availability_map[item.room_type_id] = {
                    "booked_units": booked,
                    "blocked_units": blocked,
                    "available_units": avail,
                    "is_available": avail > 0,
                }

        rating_summary = None
        if self.review_service and property_data.id:
            rating_summary = await self.review_service.get_property_rating_summary(property_data.id)

        return await self.serialize_property(
            property_data,
            vendor_email_disabled=True,
            availability_map=availability_map,
            rating_summary=rating_summary,
        )