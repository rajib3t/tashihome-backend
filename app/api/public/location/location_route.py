from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.locations.public.location import PublicLocationQueryDTO
from app.application.use_case.public.location.get_locations_use_case import (
    PublicGetLocationsUseCase,
    PublicGetLocationUseCase,
)
from app.deps.public.location import (
    get_public_get_locations_use_case,
    get_public_get_location_use_case,
)
from app.schemas.location_schema import (
    LocationListResponseSchema,
    LocationResponseSchema,
)
from app.utils.exception_decorate import handle_api_exceptions


class PublicLocationController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/locations",
            tags=["Public - Locations"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._get_locations,
                {
                    "response_model": LocationListResponseSchema,
                    "response_model_by_alias": False,
                },
            ),
            (
                "get",
                "/{slug}",
                self._get_location,
                {
                    "response_model": LocationResponseSchema,
                    "response_model_by_alias": False,
                },
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_locations(
        self,
        params: PublicLocationQueryDTO = Depends(),
        use_case: PublicGetLocationsUseCase = Depends(get_public_get_locations_use_case),
    ):
        locations = await use_case.execute(params)
        return self.build_response(
            message="Locations retrieved successfully.",
            data=locations.items,
            meta=self.pagination_meta(locations),
        )

    @handle_api_exceptions
    async def _get_location(
        self,
        slug: str,
        use_case: PublicGetLocationUseCase = Depends(get_public_get_location_use_case),
    ):
        location = await use_case.execute(slug)
        return self.build_response(
            message="Location retrieved successfully.",
            data=location,
        )


controller = PublicLocationController()
router = controller.router

