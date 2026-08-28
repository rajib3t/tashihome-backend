from app.application.dto.locations.location import LocationQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.location_model import Location, LocationStatus
from app.repositories.base_repository import Page
from app.schemas.location_schema import LocationSchema
from app.services.city_service import CityService
from app.services.location_service import LocationService


class GetLocationsUseCase(BaseUseCase):
    def __init__(
        self,
        service: LocationService,
        city_service: CityService,
        current_user: CurrentUser
    ):

        self.service = service
        self.current_user = current_user
        self.city_service = city_service
    async def execute(self, params: LocationQueryDTO) -> Page[Location]:
        filters = list(params.filters or [])
        
        if params.name:
            filters.append({"name": "name", "value": params.name})


        if params.city_id:
            city = await self.city_service.get_by_public_id(params.city_id)
            if not city:
                raise AppException(
                    status_code=404,
                    message="City not found.",
                    field="city_id",
                    error_code="CITY_NOT_FOUND",
                )
            filters.append({"name": "city_id", "value": city.id})

        if params.status:
            if params.status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID"
                )
            if params.status  == "active":
                filters.append({"name": "status", "value": LocationStatus.ACTIVE})
            elif params.status == "inactive":
                filters.append({"name": "status", "value": LocationStatus.INACTIVE})

        locations = await self.service.list(
            page=params.page,
            page_size=params.size,
            with_relations={
                "city": True,
            },
            filters=filters or None,
            flush=True,
        )

        locations.items = [
            LocationSchema.model_validate(location, from_attributes=True)
            for location in locations.items
        ]
        return locations
