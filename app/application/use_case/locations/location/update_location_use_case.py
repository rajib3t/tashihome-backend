from app.application.dto.locations.location import UpdateLocationDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.location_model import Location, LocationStatus
from app.services.city_service import CityService
from app.services.location_service import LocationService


class UpdateLocationUseCase(BaseUseCase):
    def __init__(
        self,
        service: LocationService,
        city_service: CityService,
        current_user: CurrentUser,
    ):
        self.service = service
        self.city_service = city_service
        self.current_user = current_user

    async def execute(self, location_id: str, location_data: UpdateLocationDTO) -> Location:
        existing_location = await self.service.get_by_public_id(
            public_id=location_id,
            with_relations=None,
            flush=False,
        )
        if not existing_location:
            raise AppException(
                status_code=404,
                message="Location not found",
                error_code="LOCATION_NOT_FOUND",
                field="location_id",
            )

        city = await self.city_service.get_by_public_id(
            public_id=location_data.city_id,
            with_relations=None,
            flush=False,
        )
        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city_id",
            )

        duplicate_location = await self.service.get_by_name_and_city_id(
            name=location_data.name,
            city_id=city.id,
            flush=False,
        )
        if duplicate_location and duplicate_location.id != existing_location.id:
            raise AppException(
                status_code=409,
                message="Location name already exists in this city",
                error_code="LOCATION_NAME_EXIST",
                field="name",
            )

        existing_location.name = location_data.name
        existing_location.city_id = city.id
        existing_location.updated_by = self.current_user.id

        return await self.service.update(
            existing_location,
            with_relations={"city": True},
            commit=True,
        )


class UpdateStatusLocationUseCase(BaseUseCase):
    def __init__(
        self,
        service: LocationService,
        current_user: CurrentUser,
    ):
        self.service = service
        self.current_user = current_user

    async def execute(self, location_id: str, status: str) -> Location:
        existing_location = await self.service.get_by_public_id(
            public_id=location_id,
            with_relations=None,
            flush=False,
        )
        if not existing_location:
            raise AppException(
                status_code=404,
                message="Location not found",
                error_code="LOCATION_NOT_FOUND",
                field="location_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        existing_location.status = (
            LocationStatus.ACTIVE
            if normalized_status == "active"
            else LocationStatus.INACTIVE
        )
        existing_location.updated_by = self.current_user.id

        return await self.service.update(
            existing_location,
            with_relations={"city": True},
            commit=True,
        )
