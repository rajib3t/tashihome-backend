from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.attributes.facility import FacilityDTO, FacilityQueryDTO
from app.application.use_case.vendor.attributes.facility.create_vendor_facility_use_case import VendorCreateFacilityUseCase
from app.application.use_case.vendor.attributes.facility.delete_vendor_facility_use_case import VendorDeleteFacilityUseCase
from app.application.use_case.vendor.attributes.facility.list_vendor_facilities_use_case import VendorListFacilitiesUseCase
from app.application.use_case.vendor.attributes.facility.update_vendor_facility_status_use_case import VendorUpdateFacilityStatusUseCase
from app.application.use_case.vendor.attributes.facility.update_vendor_facility_use_case import VendorUpdateFacilityUseCase
from app.deps.facility import (
    get_vendor_create_facility_use_case,
    get_vendor_delete_facility_use_case,
    get_vendor_list_facilities_use_case,
    get_vendor_update_facility_use_case,
    get_vendor_update_status_facility_use_case,
)
from app.schemas.facility_schema import FacilityListResponseSchema, FacilityResponseSchema
from app.schemas.response import BaseResponse
from app.utils.exception_decorate import handle_api_exceptions


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
            ("post", "/", self._create_facility, {"response_model": FacilityResponseSchema, "status_code": 201}),
            ("put", "/{facility_id}", self._update_facility, {"response_model": FacilityResponseSchema}),
            ("delete", "/{facility_id}", self._delete_facility, {"response_model": BaseResponse}),
            ("patch", "/{facility_id}/{status}", self._update_facility_status, {"response_model": FacilityResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_facilities(
        self,
        params: FacilityQueryDTO = Depends(),
        use_case: VendorListFacilitiesUseCase = Depends(get_vendor_list_facilities_use_case),
    ):
        facilities = await use_case.execute(params)
        return self.build_response(
            message="Facilities retrieved successfully.",
            data=facilities.items,
            meta=self.pagination_meta(facilities),
        )

    @handle_api_exceptions
    async def _create_facility(
        self,
        name: str = Form(...),
        icon: Optional[UploadFile] = File(None),
        use_case: VendorCreateFacilityUseCase = Depends(get_vendor_create_facility_use_case),
    ):
        payload = FacilityDTO(name=name, icon=icon)
        facility = await use_case.execute(payload)
        return self.build_response(
            message="Facility created successfully.",
            data=facility,
        )

    @handle_api_exceptions
    async def _update_facility(
        self,
        facility_id: str,
        name: str = Form(...),
        icon: Optional[UploadFile] = File(None),
        use_case: VendorUpdateFacilityUseCase = Depends(get_vendor_update_facility_use_case),
    ):
        payload = FacilityDTO(name=name, icon=icon)
        facility = await use_case.execute(facility_id, payload)
        return self.build_response(
            message="Facility updated successfully.",
            data=facility,
        )

    @handle_api_exceptions
    async def _delete_facility(
        self,
        facility_id: str,
        use_case: VendorDeleteFacilityUseCase = Depends(get_vendor_delete_facility_use_case),
    ):
        await use_case.execute(facility_id)
        return self.build_response(
            message="Facility deleted successfully.",
        )

    @handle_api_exceptions
    async def _update_facility_status(
        self,
        facility_id: str,
        status: str,
        use_case: VendorUpdateFacilityStatusUseCase = Depends(get_vendor_update_status_facility_use_case),
    ):
        facility = await use_case.execute(facility_id, status)
        return self.build_response(
            message="Facility status updated successfully.",
            data=facility,
        )


controller = VendorFacilityController()
router = controller.router