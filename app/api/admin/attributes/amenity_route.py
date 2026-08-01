from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Optional

from app.api.base_controller import BaseController
from app.application.dto.attributes.amenity import AmenityDTO, AmenityQueryDTO
from app.application.use_case.admin.attributes.attribute.create_amenity_use_base import CreateAmenityUseCase
from app.application.use_case.admin.attributes.attribute.get_amenity_use_case import ListAmenitiesUseCase
from app.application.use_case.admin.attributes.attribute.update_amenity_use_case import UpdateAmenityUseCase, UpdateStatusAmenityUseCase
from app.deps.amenity import get_create_amenity_use_case, get_list_amenities_use_case, get_update_amenity_use_case, get_update_status_amenity_use_case
from app.schemas.amenity_schema import AmenityListResponseSchema, AmenityResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AmenityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/amenities",
            tags=["Amenities"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_amenities, {"response_model": AmenityListResponseSchema}),
            ("post", "/", self._create_amenity, {"response_model": AmenityResponseSchema, "status_code": 201}),
            ("put", "/{amenity_id}", self._update_amenity, {"response_model": AmenityResponseSchema}),
            ("patch", "/{amenity_id}/{status}", self._update_amenity_status, {"response_model": AmenityResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_amenities(
        self,
        params: AmenityQueryDTO = Depends(),
        use_case: ListAmenitiesUseCase = Depends(get_list_amenities_use_case),
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
        use_case: CreateAmenityUseCase = Depends(get_create_amenity_use_case),
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
        use_case: UpdateAmenityUseCase = Depends(get_update_amenity_use_case),
    ):
        payload = AmenityDTO(name=name, icon=icon)
        amenity = await use_case.execute(amenity_id, payload)
        return self.build_response(
            message="Amenity updated successfully.",
            data=amenity,
        )

    @handle_api_exceptions
    async def _update_amenity_status(
        self,
        amenity_id: str,
        status: str,
        use_case: UpdateStatusAmenityUseCase = Depends(get_update_status_amenity_use_case),
    ):
        amenity = await use_case.execute(amenity_id, status)
        return self.build_response(
            message="Amenity status updated successfully.",
            data=amenity,
        )


controller = AmenityController()
router = controller.router
