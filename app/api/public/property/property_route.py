from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.api.base_controller import BaseController
from fastapi import APIRouter, Depends
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.deps.public.property import public_properties_use_case
from app.schemas.public.property_schema import PublicPropertyResponseListSchema
from app.utils.exception_decorate import handle_api_exceptions  
class PublicPropertyController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/public/properties",
            tags=["Public Properties"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_properties, {"response_model": PublicPropertyResponseListSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_properties(
        self,
        params: PublicPropertyQueryDTO = Depends(),
        use_case: PublicPropertiesUseCase = Depends(public_properties_use_case),
    ):
        properties = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties.items,
            meta=self.pagination_meta(properties),
        )

controller = PublicPropertyController()
router = controller.router