from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.attributes.amenity import AmenityDTO, AmenityQueryDTO
from app.application.use_case.vendor.attributes.amenity.create_vendor_amenity_use_case import VendorCreateAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.delete_vendor_amenity_use_case import VendorDeleteAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.list_vendor_amenities_use_case import VendorListAmenitiesUseCase
from app.application.use_case.vendor.attributes.amenity.update_vendor_amenity_status_use_case import VendorUpdateAmenityStatusUseCase
from app.application.use_case.vendor.attributes.amenity.update_vendor_amenity_use_case import VendorUpdateAmenityUseCase
from app.deps.amenity import (
    get_vendor_create_amenity_use_case,
    get_vendor_delete_amenity_use_case,
    get_vendor_list_amenities_use_case,
    get_vendor_update_amenity_use_case,
    get_vendor_update_status_amenity_use_case,
)
from app.schemas.amenity_schema import AmenityListResponseSchema, AmenityResponseSchema
from app.schemas.response import BaseResponse
from app.utils.exception_decorate import handle_api_exceptions


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
            ("post", "/", self._create_amenity, {"response_model": AmenityResponseSchema, "status_code": 201}),
            ("put", "/{amenity_id}", self._update_amenity, {"response_model": AmenityResponseSchema}),
            ("delete", "/{amenity_id}", self._delete_amenity, {"response_model": BaseResponse}),
            ("patch", "/{amenity_id}/{status}", self._update_amenity_status, {"response_model": AmenityResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_amenities(
        self,
        params: AmenityQueryDTO = Depends(),
        use_case: VendorListAmenitiesUseCase = Depends(get_vendor_list_amenities_use_case),
    ):
        amenities = await use_case.execute(params)
        return self.build_response(
            message="Amenities retrieved successfully.",
            data=amenities.items,
            meta=self.pagination_meta(amenities),
        )

    @handle_api_exceptions
    async def _create_amenity(
        self,
        name: str = Form(...),
        icon: Optional[UploadFile] = File(None),
        use_case: VendorCreateAmenityUseCase = Depends(get_vendor_create_amenity_use_case),
    ):
        payload = AmenityDTO(name=name, icon=icon)
        amenity = await use_case.execute(payload)
        return self.build_response(
            message="Amenity created successfully.",
            data=amenity,
        )

    @handle_api_exceptions
    async def _update_amenity(
        self,
        amenity_id: str,
        name: str = Form(...),
        icon: Optional[UploadFile] = File(None),
        use_case: VendorUpdateAmenityUseCase = Depends(get_vendor_update_amenity_use_case),
    ):
        payload = AmenityDTO(name=name, icon=icon)
        amenity = await use_case.execute(amenity_id, payload)
        return self.build_response(
            message="Amenity updated successfully.",
            data=amenity,
        )

    @handle_api_exceptions
    async def _delete_amenity(
        self,
        amenity_id: str,
        use_case: VendorDeleteAmenityUseCase = Depends(get_vendor_delete_amenity_use_case),
    ):
        await use_case.execute(amenity_id)
        return self.build_response(
            message="Amenity deleted successfully.",
        )

    @handle_api_exceptions
    async def _update_amenity_status(
        self,
        amenity_id: str,
        status: str,
        use_case: VendorUpdateAmenityStatusUseCase = Depends(get_vendor_update_status_amenity_use_case),
    ):
        amenity = await use_case.execute(amenity_id, status)
        return self.build_response(
            message="Amenity status updated successfully.",
            data=amenity,
        )


controller = VendorAmenityController()
router = controller.router