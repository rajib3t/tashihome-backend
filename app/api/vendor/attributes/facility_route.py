from app.api.base_controller import BaseController

from app.application.dto.attributes.facility import FacilityQueryDTO
from app.application.use_case.admin.attributes.attribute.get_facility_use_case import ListFacilitiesUseCase
from app.deps.facility import get_vendor_list_facilities_use_case
from app.schemas.facility_schema import FacilityListResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from fastapi import APIRouter, Depends

class VendorFacilityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/facilities",
            tags=["Vendor - Facilities"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_facilities, {"response_model": FacilityListResponseSchema}),
            ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_facilities(
        self,
        params: FacilityQueryDTO = Depends(),
        use_case : ListFacilitiesUseCase = Depends(get_vendor_list_facilities_use_case)
        ):
        facilities = await use_case.execute(params)

        return self.build_response(
            message="Facilities retrieved successfully.",
            data=facilities.items,
            meta=self.pagination_meta(facilities),
        )

controller = VendorFacilityController()
router = controller.router