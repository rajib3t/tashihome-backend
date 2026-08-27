from app.api.base_controller import BaseController
from app.application.dto.properties.property import PropertyQueryDTO
from app.utils.exception_decorate import handle_api_exceptions
from fastapi import APIRouter, Depends

class PropertyController(BaseController):
    def __init__(self):
            self.router = APIRouter(
                prefix="/properties",
                tags=["Vendor - Properties"],
            )
            self._register_routes()
    
    def _register_routes(self):
        routes = [
            
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_properties(
        self,
        params: PropertyQueryDTO = Depends(),
        use_case: GetPropertiesUseCase = Depends(get_property_list_use_case),
    ):
        properties = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties.items,
            meta=self.pagination_meta(properties),
        )