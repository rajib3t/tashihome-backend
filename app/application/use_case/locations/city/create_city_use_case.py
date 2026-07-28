from app.services.country_service import CountryService
from app.core.exceptions import AppException
from app.application.use_case.base_use_case import BaseUseCase
from app.models.city_model import City
from app.application.dto.locations.city import CityDTO
from app.deps.auth import CurrentUser
from app.services.storage_service import StorageService
from app.services.city_service import CityService
class CreateCityUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "image_url": {
            "allowed_prefixes": ("image/",),
            "max_size_bytes": 2 * 1024 * 1024,
        },
    }
    
    def __init__(
        self,
        service : CityService,
        storage_service : StorageService,
        country_service : CountryService,
        current_user : CurrentUser,
        ):
        self.city_service = service
        self.storage_service = storage_service
        self.current_user = current_user
        self.country_service = country_service
    
    async def execute(self, city_data: CityDTO ) -> City:
        payload = {
            "name": city_data.name,
            "country_id": city_data.country_id,
            "image_url": city_data.image_url,
        }

        if await self.city_service.get_by_name(payload["name"].lower()):
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )
        if self._is_upload_file(payload.get("image_url")):
            payload["image_url"] = await self._upload_file(
                payload["image_url"], folder="cities", field_name="image_url"
            )
        
        country = await self.country_service.get_by_public_id(
            public_id=payload["country_id"], with_relations=None, flush=True
        )
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country_id",
            )

        city_obj = City(
            name=payload["name"],
            image_url=payload["image_url"],
            country_id=country.id,
            created_by = self.current_user.id,
            updated_by = self.current_user.id
        )
        city = await self.city_service.create(
            city_obj,   
            with_relations={
                "country" : True
            }, 
            commit=True
        )
        return city 
        
        
