from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Optional
from app.api.base_controller import BaseController
from app.application.dto.attributes.facility import  FacilityDTO, FacilityQueryDTO
from app.application.use_case.attributes.attribute.create_facility_use_base import  CreateFacilityUseCase
from app.application.use_case.attributes.attribute.get_facility_use_case import ListFacilitiesUseCase
from app.application.use_case.attributes.attribute.update_facility_use_case import UpdateFacilityUseCase, UpdateStatusFacilityUseCase
from app.deps.facility import  get_create_facility_use_case, get_list_facilities_use_case, get_update_facility_use_case, get_update_status_facility_use_case
from app.schemas.facility_schema import  FacilityListResponseSchema, FacilityResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class FacilityController(BaseController):
    def __init__(self):
        self.router = APIRouter(
                    prefix="/facilities",
                    tags=["Facilities"],
                )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_facilities, {"response_model": FacilityListResponseSchema}),
            ("post", "/", self._create_facility, {"response_model": FacilityResponseSchema, "status_code": 201}),
            ("put", "/{facility_id}", self._update_facility, {"response_model": FacilityResponseSchema}),
            ("patch", "/{facility_id}/{status}", self._update_facility_status, {"response_model": FacilityResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_facilities(
        self,
        params: FacilityQueryDTO = Depends(),
        use_case : ListFacilitiesUseCase = Depends(get_list_facilities_use_case)
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
        icon : Optional[UploadFile] = File(None),
        use_case : CreateFacilityUseCase = Depends(get_create_facility_use_case)
        ):
        payload = FacilityDTO(
            name=name,
            icon=icon,
        )
        
        attribute = await use_case.execute(payload)

        return self.build_response(
            message="Facility created successfully.",
            data=attribute,
        )

    @handle_api_exceptions
    async def _update_facility(
        self,
        facility_id: str,
        name: str = Form(...),
        icon: Optional[UploadFile] = File(None),
        use_case: UpdateFacilityUseCase = Depends(get_update_facility_use_case),
    ):
        payload = FacilityDTO(
            name=name,
            icon=icon,
        )
        attribute = await use_case.execute(facility_id, payload)

        return self.build_response(
            message="Facility updated successfully.",
            data=attribute,
        )

    @handle_api_exceptions
    async def _update_facility_status(
        self,
        facility_id: str,
        status: str,
        use_case: UpdateStatusFacilityUseCase = Depends(get_update_status_facility_use_case),
    ):
        attribute = await use_case.execute(facility_id, status)

        return self.build_response(
            message="Facility status updated successfully.",
            data=attribute,
        )

controller = FacilityController()
router = controller.router
