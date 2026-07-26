from app.application.dto.locations.country import CountryQueryDTO
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.country_model import CountryStatus
from app.services.country_service import CountryService


class GetCountriesUseCase:
    
    def __init__(
        self,
        country_service: CountryService,
        current_user: CurrentUser
    ):
        self.country_service = country_service
        self.current_user = current_user

    async def execute(self, request_dto: CountryQueryDTO):
        filters = list(request_dto.filters or [])

        # Allow the API to support simple `?name=...` searches without forcing
        # clients to build the structured filters payload.
        if request_dto.name:
            filters.append({"name": "name", "value": request_dto.name})

        # Only apply code filtering when the provided code actually exists.
        # Otherwise, keep the normal list response instead of returning no rows.
        if request_dto.code:
           
            filters.append({"name": "code", "value": request_dto.code})

        if request_dto.status:
            if request_dto.status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID"
                )
            if request_dto.status  == "active":
                filters.append({"name": "status", "value": CountryStatus.ACTIVE})
            elif request_dto.status == "inactive":
                filters.append({"name": "status", "value": CountryStatus.INACTIVE})


        countries = await self.country_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            with_relations={
                "cities": True
            },
            filters=filters or None,
            flush=True
        )
        
        return countries
