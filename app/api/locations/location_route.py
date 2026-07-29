from app.api.base_controller import BaseController
from fastapi import APIRouter
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
    ):
        pass


controller = LocationController()
router = controller.router
