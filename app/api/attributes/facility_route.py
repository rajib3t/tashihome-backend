from fastapi import APIRouter, Depends, File, Form, UploadFile
from typing import Optional
from app.api.base_controller import BaseController
from app.application.dto.attributes.facility import  FacilityDTO
from app.application.use_case.attributes.attribute.create_facility_use_base import  CreateFacilityUseCase
from app.deps.facility import  get_create_facility_use_case
from app.schemas.facility_schema import  FacilityResponseSchema
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
            ("post", "/", self._create_facility, {"response_model": FacilityResponseSchema, "status_code": 201}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


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

controller = FacilityController()
router = controller.router