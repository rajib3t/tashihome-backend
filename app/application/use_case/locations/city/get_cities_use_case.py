from app.application.dto.locations.city import CityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.city_model import City, CityStatus
from app.repositories.base_repository import Page
from app.schemas.city_schema import CitySchema
from app.services.city_service import CityService
from app.services.country_service import CountryService
from app.services.storage_service import StorageService


class GetCitiesUseCase(BaseUseCase):
    def __init__(
        self,
        service: CityService,
        storage_service: StorageService,
        country_service: CountryService,
        current_user: CurrentUser,
    ):
        self.city_service = service
        self.storage_service = storage_service
        self.country_service = country_service
        self.current_user = current_user

    async def execute(self, request_dto: CityQueryDTO) ->Page[City]:
        filters = list(request_dto.filters or [])

        if request_dto.name:
            filters.append({"name": "name", "value": request_dto.name})

        if request_dto.country_id:
            country = await self.country_service.get_by_public_id(request_dto.country_id)
            if not country:
                raise AppException(
                    status_code=404,
                    message="Country not found.",
                    field="country_id",
                    error_code="COUNTRY_NOT_FOUND",
                )
            filters.append({"name": "country_id", "value": country.id})

        if request_dto.status:
            if request_dto.status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
            if request_dto.status == "active":
                filters.append({"name": "status", "value": CityStatus.ACTIVE})
            elif request_dto.status == "inactive":
                filters.append({"name": "status", "value": CityStatus.INACTIVE})

        cities = await self.city_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            with_relations={
                "country": True,
            },
            filters=filters or None,
            flush=True,
        )

        items = []
        for city in cities.items:
            city_schema = CitySchema.model_validate(city, from_attributes=True)
            if city_schema.image_url:
                city_schema.image_url = self.storage_service.generate_presigned_url(city_schema.image_url)
            items.append(city_schema)

        cities.items = items
        return cities
        
