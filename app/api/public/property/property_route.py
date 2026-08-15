from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.api.base_controller import BaseController
from fastapi import APIRouter, Depends
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.deps.public.property import public_get_property_use_case, public_properties_use_case
from app.schemas.public.property_schema import PublicPropertyResponse, PublicPropertyResponseListSchema
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
            ("get", "/{slug}", self._get_property, {"response_model": PublicPropertyResponse}),
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
    @handle_api_exceptions
    async def _get_property(
            
        self,
        slug: str,
        use_case: PublicGetPropertyUseCase = Depends(public_get_property_use_case),
    ):
        property_data = await use_case.execute(slug)
        return self.build_response(
            message="Property retrieved successfully.",
            data=property_data,
        )

controller = PublicPropertyController()
router = controller.router