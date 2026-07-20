from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController

from app.application.dto.locations.country import CountryDTO, CountryQueryDTO
from app.application.use_case.locations.country.create_country_use_case import CreateCountryUseCase
from app.deps.locations import get_countries_use_case, get_create_country_use_case
from app.schemas.country_schema import CountryListResponseSchema, CountryResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from app.application.use_case.locations.country.get_countries_use_case import GetCountriesUseCase

class CountryController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/countries",
            tags=["Countries"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_countries, {"response_model": CountryListResponseSchema, "response_model_by_alias": False}),
            ("post", "/", self._create_country, {"response_model":CountryResponseSchema, "response_model_by_alias": False, "status_code": 201}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_countries(
        self,
        params: CountryQueryDTO = Depends(),
        use_case: GetCountriesUseCase = Depends(get_countries_use_case)
    ):
        countries = await use_case.execute(params)
        return self.build_response(
            data=countries.items,
            message="Countries retrieved successfully.",
            meta=self.pagination_meta(countries)
        )

    @handle_api_exceptions
    async def _create_country(
        self,
        country_data: CountryDTO,
        use_case: CreateCountryUseCase = Depends(get_create_country_use_case)
    ):
        # Placeholder for country creation logic
        result = await use_case.execute(country_data)
        return self.build_response(
            message="Country created successfully.",
            data=result
        )

controller = CountryController()
router = controller.router
