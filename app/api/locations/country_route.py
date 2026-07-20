from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController

from app.application.dto.locations.country import CountryQueryDTO
from app.deps.locations import get_countries_use_case
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
            ("get", "/", self._get_countries, {"response_model": dict, "response_model_by_alias": False}),
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
            data=countries,
            message="Countries retrieved successfully."
        )


controller = CountryController()
router = controller.router
