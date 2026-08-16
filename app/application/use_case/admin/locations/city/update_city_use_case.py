from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.utils.validation import find_similar_name
from app.deps.auth import CurrentUser
from app.models.city_model import City, CityStatus
from app.services.city_service import CityService
from app.services.country_service import CountryService
from app.services.storage_service import StorageService
from app.application.dto.locations.city import CityDTO
import copy


class UpdateCityUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "image_url": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg"),
            "max_size_bytes": 2 * 1024 * 1024,
        },
    }
    def __init__(
            self,
            service: CityService,
            country_service: CountryService,
            storage_service : StorageService,
            current_user : CurrentUser

    ): 
        self.service = service
        self.country_service = country_service
        self.storage_service = storage_service
        self.current_user = current_user

    
    async def execute(self, city_id: str, data: CityDTO) -> City:
        existing_city = await self.service.get_by_public_id(
            public_id=city_id, with_relations=None, flush=False
        )

        if not existing_city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city_id",
            )
        duplicate_name = await self.service.get_by_name(
            name=data.name.lower(),
            with_relations=None,
            flush=False,
        )
        if duplicate_name and duplicate_name.id != existing_city.id:
            raise AppException(
                status_code=409,
                message="City already exists",
                error_code="CITY_ALREADY_EXISTS",
                field="name",
            )

        existing_cities = await self.service.get_all()
        existing_names = [c.name for c in existing_cities if c.id != existing_city.id]
        similar_name = find_similar_name(data.name, existing_names)
        if similar_name:
            raise AppException(
                status_code=409,
                message=f"City name is too similar to an existing city: '{similar_name}'.",
                error_code="CITY_NAME_TOO_SIMILAR",
                field="name",
            )

        country = await self.country_service.get_by_public_id(
            public_id=data.country_id,
            with_relations=None,
            flush=False,
        )
        if not country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country_id",
            )

        image_url = data.image_url
        if self._is_upload_file(image_url):
            old_image_url = existing_city.image_url
            image_url = await self._upload_file(
                image_url, folder="cities", field_name="image_url", webp=True
            )
            if isinstance(old_image_url, str) and old_image_url:
                try:
                    await self.storage_service.delete_object(old_image_url)
                except Exception:
                    pass
        elif image_url is None:
            image_url = existing_city.image_url

        existing_city.name = data.name
        existing_city.country_id = country.id
        existing_city.image_url = image_url
        existing_city.updated_by = self.current_user.id
        existing_city.short_description = data.short_description
        existing_city.tag_line = data.tag_line
        is_featured = bool(data.is_featured)
        if isinstance(data.is_featured, str):
            is_featured = data.is_featured.strip().lower() in ("true", "1", "yes", "t")
        existing_city.is_featured = is_featured

        if is_featured:
            features = await self.service.get_city_with_is_featured(with_relations={"country" : True})
            other_featured = [f for f in features if f.id != existing_city.id]
            if len(other_featured) >= 4:
                raise AppException(
                    status_code=409,
                    message="Already 4 featured cities exist",
                    error_code="FEATURED_CITIES_LIMIT_EXCEEDED",
                    field="is_featured",
                )

        city = await self.service.update(
            existing_city,
            with_relations={"country": True},
            commit=True,
        )
        
        if city.image_url:
            display_city = copy.copy(city)
            display_city.image_url = city.image_url
            return display_city
        
        return city


class UpdateStatusCityUseCase(BaseUseCase):
    def __init__(
            self,
            service: CityService,
            current_user: CurrentUser
        ):
        self.service = service
        self.current_user = current_user


    async def execute(self, city_id: str, status: bool) -> City:
        existing_city = await self.service.get_by_public_id(
            public_id=city_id, with_relations=None, flush=False
        )

        if not existing_city:
            raise AppException(
                status_code=404,
                message="City not found",
                error_code="CITY_NOT_FOUND",
                field="city_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )
        
        existing_city.status = (
            CityStatus.ACTIVE if normalized_status == "active" else CityStatus.INACTIVE
        )
        existing_city.updated_by = self.current_user.id

        return await self.service.update(
            city_data=existing_city,
            with_relations={"country": True},
            commit=True,
        )
        
