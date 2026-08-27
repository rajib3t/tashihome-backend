from fastapi import APIRouter, Depends
from app.api.base_controller import BaseController
from app.application.dto.locations.city import CityQueryDTO
from app.application.use_case.admin.locations.city.get_cities_use_case import GetCitiesUseCase
from app.deps.locations import get_city_list_use_case
from app.schemas.city_schema import CityListResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class VendorCityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/cities",
            tags=["Vendor - Cities"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_cities, {"response_model": CityListResponseSchema, "response_model_by_alias": False}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_cities(
        self,
        params: CityQueryDTO = Depends(),
        use_case: GetCitiesUseCase = Depends(get_city_list_use_case),
    ):
        cities = await use_case.execute(params)
        return self.build_response(
            message="Cities retrieved successfully.",
            data=cities.items,
            meta=self.pagination_meta(cities),
        )


controller = VendorCityController()
router = controller.router
