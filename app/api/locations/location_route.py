from fastapi.params import Depends

from app.api.base_controller import BaseController
from fastapi import APIRouter
from app.application.use_case.locations.location.create_location_use_case import CreateLocationUseCase
from app.deps.locations import get_create_location_use_case
from app.utils.exception_decorate import handle_api_exceptions
from app.schemas.location_schema import LocationsResponseSchema, LocationResponseSchema
from app.application.dto.locations.location import LocationDTO

class LocationController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/locations",
            tags=["Locations"],
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
            )
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    
    @handle_api_exceptions
    async def _get_locations(self):
        pass

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


controller = LocationController()
router = controller.router
