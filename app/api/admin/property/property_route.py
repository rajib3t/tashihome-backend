from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.properties.property import PropertyDTO, PropertyQueryDTO, PropertyUpdateDTO
from app.application.use_case.admin.properties.property_use_case import (
    ListPropertiesUseCase,
    UpdatePropertyUseCase,
    UpdateStatusPropertyUseCase,
)
from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
from app.deps.property import (
    get_create_property_use_case,
    get_list_properties_use_case,
    get_update_property_status_use_case,
    get_update_property_use_case,
)
from app.schemas.property_schema import PropertyListResponseSchema, PropertyResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PropertyController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/properties",
            tags=["Properties"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_properties, {"response_model": PropertyListResponseSchema}),
            ("post", "/", self._create_property, {"response_model": PropertyResponseSchema, "status_code": 201}),
            ("put", "/{property_id}", self._update_property, {"response_model": PropertyResponseSchema}),
            ("patch", "/{property_id}/{status}", self._update_property_status, {"response_model": PropertyResponseSchema}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_properties(
        self,
        params: PropertyQueryDTO = Depends(),
        use_case: ListPropertiesUseCase = Depends(get_list_properties_use_case),
    ):
        properties_page = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties_page.items,
            meta=self.pagination_meta(properties_page),
        )

    @handle_api_exceptions
    async def _create_property(
        self,
        data: PropertyDTO,
        use_case: CreatePropertyUseCase = Depends(get_create_property_use_case),
    ):
        created_property = await use_case.execute(data)
        return self.build_response(
            message="Property created successfully.",
            data=created_property,
        )

    @handle_api_exceptions
    async def _update_property(
        self,
        property_id: str,
        data: PropertyUpdateDTO,
        use_case: UpdatePropertyUseCase = Depends(get_update_property_use_case),
    ):
        updated_property = await use_case.execute(property_id, data)
        return self.build_response(
            message="Property updated successfully.",
            data=updated_property,
        )

    @handle_api_exceptions
    async def _update_property_status(
        self,
        property_id: str,
        status: str,
        use_case: UpdateStatusPropertyUseCase = Depends(get_update_property_status_use_case),
    ):
        updated_property = await use_case.execute(property_id, status)
        return self.build_response(
            message="Property status updated successfully.",
            data=updated_property,
        )


controller = PropertyController()
router = controller.router
