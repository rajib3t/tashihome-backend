from typing import Optional

from app.application.dto.locations.country import CountryDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.country_model import Country, CountryStatus
from app.services.country_service import CountryService


class UpdateCountryUseCase:
    def __init__(
            self,
            country_service: CountryService,
            current_user:CurrentUser
    ):
        self.country_service = country_service
        self.current_user = current_user

    async def execute(self, country_id: str, country_data: CountryDTO) -> Optional[Country]:
        existing_country = await self.country_service.get_by_public_id(
            public_id=country_id, with_relations=None, flush=False
        )
        if not existing_country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country_id",
            )

        duplicate_name = await self.country_service.get_by_name(
            name=country_data.name.lower(),
            with_relations=None,
            flush=False,
        )
        if duplicate_name and duplicate_name.id != existing_country.id:
            raise AppException(
                status_code=409,
                message="Country name already exists",
                error_code="COUNTRY_NAME_EXIST",
                field="name",
            )

        duplicate_code = await self.country_service.get_by_code(
            code=country_data.code.upper(),
            with_relations=None,
            flush=False,
        )
        if duplicate_code and duplicate_code.id != existing_country.id:
            raise AppException(
                status_code=409,
                message="Country code already exists",
                error_code="COUNTRY_CODE_EXIST",
                field="code",
            )

        existing_country.name = country_data.name
        existing_country.code = country_data.code
        existing_country.updated_by = self.current_user.id

        updated_country = await self.country_service.update_country(existing_country)

        return updated_country
        

class UpdateStatusCountryUseCase:
    def __init__(
            self,
            country_service: CountryService,
            current_user:CurrentUser
    ):
        self.country_service = country_service
        self.current_user = current_user

    async def execute(self, country_id: str, status: str) -> Optional[Country]:
        existing_country = await self.country_service.get_by_public_id(
            public_id=country_id, with_relations=None, flush=False
        )
        if not existing_country:
            raise AppException(
                status_code=404,
                message="Country not found",
                error_code="COUNTRY_NOT_FOUND",
                field="country_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive"]:
            raise AppException(
                status_code=422,
                message="Status must be either 'active' or 'inactive'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        existing_country.status = (
            CountryStatus.ACTIVE if normalized_status == "active" else CountryStatus.INACTIVE
        )
        existing_country.updated_by = self.current_user.id

        updated_country = await self.country_service.update_country(existing_country)

        return updated_country
