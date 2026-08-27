from app.schemas.city_schema import CityListResponseSchema, CityResponseSchema
from app.deps.public.city import get_public_get_cities_use_case
from app.application.use_case.public.city.get_cities_use_case import PublicGetCitiesUseCase
from app.utils.exception_decorate import handle_api_exceptions
from app.application.dto.locations.public.city import PublicCityQueryDTO
from fastapi import APIRouter, Depends
from app.api.base_controller import BaseController


class PublicCityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/cities",
            tags=["Public - Cities"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_cities, {"response_model": CityListResponseSchema, "response_model_by_alias": False}),
            ("get", "/{slug}", self._get_city, {"response_model": CityResponseSchema, "response_model_by_alias": False}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)
    @handle_api_exceptions
    async def _get_cities(
        self,
        params: PublicCityQueryDTO = Depends(),
        use_case: PublicGetCitiesUseCase = Depends(get_public_get_cities_use_case),
    ):
        cities = await use_case.execute(params)
        return self.build_response(
            message="Cities retrieved successfully.",
            data=cities.items,
            meta=self.pagination_meta(cities),
        )
        
    @handle_api_exceptions
    async def _get_city(
        self,
        slug: str,
        # use_case: PublicGetPropertyUseCase = Depends(public_get_property_use_case),
    ):
        # property_data = await use_case.execute(slug)
        # return self.build_response(
        #     message="Property retrieved successfully.",
        #     data=property_data,
        # )
        pass

controller = PublicCityController()
router = controller.router
    