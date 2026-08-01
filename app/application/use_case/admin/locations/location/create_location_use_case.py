from app.application.dto.locations.location import LocationDTO
from app.core.exceptions import AppException
from app.application.use_case.base_use_case import BaseUseCase
from app.models.location_model import Location
from app.services.location_service import LocationService
from app.services.city_service import CityService
from app.deps.auth import CurrentUser

class CreateLocationUseCase(BaseUseCase):
    def __init__(
        self,
        service: LocationService,
        city_service : CityService,
        current_user : CurrentUser
    ):
        self.service = service
        self.city_service = city_service
        self.current_user = current_user
    
    async def execute(self, location_data: LocationDTO) -> Location:
        city = await self.city_service.get_by_public_id(
            public_id=location_data.city_id,
            with_relations={"country": True},
            flush=True,
        )
        if not city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city_id",
            )

        existing_location = await self.service.location_repository.get_by_name_and_city_id(
            name=location_data.name,
            city_id=city.id,
            flush=True,
        )
        if existing_location:
            raise AppException(
                status_code=409,
                message="Location name already exists in this city",
                error_code="LOCATION_NAME_EXIST",
                field="name",
            )

        location = Location(
            name=location_data.name,
            city_id=city.id,
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )
        created_location = await self.service.create(
            location,
            with_relations=None,
            commit=True,
        )

        return await self.service.location_repository.get_by_id_with_city_country(
            created_location.id,
            flush=True,
        ) or created_location
