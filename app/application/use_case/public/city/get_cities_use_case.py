from app.models.city_model import City
from app.repositories.base_repository import Page
from app.core.exceptions import AppException
from app.services.country_service import CountryService
from app.application.dto.locations.city import CityFilterDTO
from app.application.dto.locations.public.city import PublicCityQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.services.storage_service import StorageService
from app.services.city_service import CityService
import copy
class PublicGetCitiesUseCase(BaseUseCase):
    def __init__(
        self,
        city_service: CityService,
        country_service: CountryService,
        storage_service: StorageService,
    ):
        self.city_service = city_service
        self.country_service = country_service
        self.storage_service = storage_service
    async def execute(self, params: PublicCityQueryDTO) ->Page[City]:
        filters = list(params.filters or [])

        if params.country_id:
            country = await self.country_service.get_by_public_id(params.country_id)
            if not country:
                raise AppException(
                    status_code=404,
                    message="Country not found.",
                    field="country_id",
                    error_code="COUNTRY_NOT_FOUND",
                )

            filters.append({"name": "country_id", "value": country.id})
        if params.is_featured is not None:
            filters.append({"name": "is_featured", "value": bool(params.is_featured)})
        
        filters.append({"name": "status", "value": "active"})
        cities_page = await self.city_service.list(
                page=params.page,
                page_size=params.size,
                filters=filters,
                with_relations={
                    "country": True,
                },
            )
        
        updated_items = []
        for city in cities_page.items:
            display_city = copy.copy(city)
            if city.image_url:
                display_city.image_url = await self.storage_service.get_display_url(city.image_url)
            updated_items.append(display_city)

        cities_page.items = updated_items
        return cities_page
        



        
            

        