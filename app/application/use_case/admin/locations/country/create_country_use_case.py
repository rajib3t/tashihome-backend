from app.application.dto.locations.country import CountryDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.country_model import Country
from app.services.country_service import CountryService
from app.utils.slug import generate_slug, generate_unique_slug


class CreateCountryUseCase:
    def __init__(
            self, 
            country_service: CountryService, 
            current_user: CurrentUser
        ):
        self.country_service = country_service
        self.current_user = current_user
    
    async def execute(self, country_data: CountryDTO) -> Country:
        if await self.country_service.get_by_name(
            name=country_data.name.lower(), with_relations=None, flush=True
        ):
            raise AppException(
                status_code=409,
                message="Country name already exists",
                error_code="COUNTRY_NAME_EXIST",
                field="name",
            )

        if await self.country_service.get_by_code(
            code=country_data.code.upper(), with_relations=None, flush=True
        ):
            raise AppException(
                status_code=409,
                message="Country code already exists",
                error_code="COUNTRY_CODE_EXIST",
                field="code",
            )

        base_slug = await generate_slug(country_data.slug or country_data.name)
        if not base_slug:
            raise AppException(
                status_code=422,
                message="Slug generation failed.",
                field="slug",
                error_code="SLUG_GENERATION_FAILED",
            )

        slug = await generate_unique_slug(
            base_slug,
            lambda s: self.country_service.get_by_slug(s, flush=True),
        )

        new_country = Country(
            name=country_data.name, 
            code=country_data.code,
            slug=slug,
            created_by=self.current_user.id,
            updated_by=self.current_user.id
        )

        return await self.country_service.create_country(
            new_country, with_relations=None, commit=True
        )