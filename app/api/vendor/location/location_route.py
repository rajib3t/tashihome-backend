from app.api.base_controller import BaseController
from app.application.dto.locations.location import LocationQueryDTO
from app.application.use_case.admin.locations.location.get_locations_use_case import GetLocationsUseCase
from app.deps.locations import get_vendor_list_location_use_case
from app.schemas.location_schema import LocationsResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from fastapi import Depends, APIRouter

class VendorLocationController(BaseController):
    def __init__(self):
            self.router = APIRouter(
                prefix="/locations",
                tags=["Vendor - Locations"],
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
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    async def _get_locations(
        self,
        params: LocationQueryDTO = Depends(),
        use_case: GetLocationsUseCase = Depends(get_vendor_list_location_use_case)
    ):

        results = await use_case.execute(params=params)

        return self.build_response(
            message="Locations fetch successfully",
            data=results.items,
            meta=self.pagination_meta(results)
        )

controller = VendorLocationController()
router = controller.router