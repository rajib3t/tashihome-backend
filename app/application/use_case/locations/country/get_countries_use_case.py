from app.application.dto.locations.country import CountryQueryDTO
from app.deps.auth import CurrentUser
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
        countries = await self.country_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            with_relations={
                "cities"
            },
            filters=request_dto.filters,
            flush=True
        )
        
        return countries
