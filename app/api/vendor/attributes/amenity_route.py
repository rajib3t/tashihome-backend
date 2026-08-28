from app.api.base_controller import BaseController
from app.application.dto.attributes.amenity import AmenityQueryDTO
from app.application.use_case.admin.attributes.attribute.get_amenity_use_case import ListAmenitiesUseCase
from app.deps.amenity import get_vendor_list_amenities_use_case
from app.schemas.amenity_schema import AmenityListResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from app.utils.exception_decorate import handle_api_exceptions
from fastapi import APIRouter, Depends

class VendorAmenityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/amenities",
            tags=["Vendor - Amenities"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_amenities, {"response_model": AmenityListResponseSchema}),
            
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_amenities(
        self,
        params: AmenityQueryDTO = Depends(),
        use_case: ListAmenitiesUseCase = Depends(get_vendor_list_amenities_use_case),
    ):
        amenities = await use_case.execute(params)
        return self.build_response(
            message="Amenities retrieved successfully.",
            data=amenities.items,
            meta=self.pagination_meta(amenities),
        )


controller = VendorAmenityController()
router = controller.router