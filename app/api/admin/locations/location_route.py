from fastapi.params import Depends

from app.api.base_controller import BaseController
from fastapi import APIRouter
from app.application.use_case.admin.locations.location.create_location_use_case import CreateLocationUseCase
from app.application.use_case.admin.locations.location.get_locations_use_case import GetLocationsUseCase
from app.application.use_case.admin.locations.location.update_location_use_case import UpdateLocationUseCase, UpdateStatusLocationUseCase
from app.deps.locations import (
    get_create_location_use_case,
    get_list_location_use_case,
    get_update_location_use_case,
    get_update_location_status_use_case,
)
from app.utils.exception_decorate import handle_api_exceptions
from app.schemas.location_schema import LocationsResponseSchema, LocationResponseSchema
from app.application.dto.locations.location import CountryQueryDTO, LocationDTO, UpdateLocationDTO

class LocationController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/locations",
            tags=["Admin - Locations"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get", 
                "/", 
                self._get_locations,
                {
                    "response_model": LocationsResponseSchema,
                    "response_model_by_alias": False,
                }
            ),
            (
                "post",
                "/",
                self._create_location,
                {
                    "response_model": LocationResponseSchema,
                    "response_model_by_alias": False,
                    "status_code": 201,
                }
            ),
            (
                "put",
                "/{location_id}",
                self._update_location,
                {
                    "response_model": LocationResponseSchema,
                    "response_model_by_alias": False,
                }
            ),
            (
                "patch",
                "/{location_id}/{status}",
                self._update_location_status,
                {
                    "response_model": LocationResponseSchema,
                    "response_model_by_alias": False,
                }
            )
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    
    @handle_api_exceptions
    async def _get_locations(
        self,
        params: CountryQueryDTO = Depends(),
        use_case: GetLocationsUseCase = Depends(get_list_location_use_case)
    ):

        results = await use_case.execute(params=params)

        return self.build_response(
            message="Locations fetch successfully",
            data=results.items,
            meta=self.pagination_meta(results)
        )

    @handle_api_exceptions
    async def _create_location(
        self,
        location_data: LocationDTO,
        use_case : CreateLocationUseCase = Depends(get_create_location_use_case)
    ):

        result = await use_case.execute(location_data=location_data)

        return self.build_response(
            message="Location create successfully",
            data=result
        )

    @handle_api_exceptions
    async def _update_location(
        self,
        location_id: str,
        location_data: UpdateLocationDTO,
        use_case: UpdateLocationUseCase = Depends(get_update_location_use_case),
    ):
        result = await use_case.execute(location_id, location_data)
        return self.build_response(
            message="Location updated successfully",
            data=result,
        )

    @handle_api_exceptions
    async def _update_location_status(
        self,
        location_id: str,
        status: str,
        use_case: UpdateStatusLocationUseCase = Depends(get_update_location_status_use_case),
    ):
        result = await use_case.execute(location_id, status)
        return self.build_response(
            message="Location status updated successfully",
            data=result,
        )


controller = LocationController()
router = controller.router
