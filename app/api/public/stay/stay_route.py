from fastapi import APIRouter, Depends
from app.api.base_controller import BaseController
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.deps.public.stay import public_get_stay_use_case, public_search_stays_use_case
from app.schemas.public.stay_schema import PublicStayListResponseSchema, PublicStayResponse
from app.utils.exception_decorate import handle_api_exceptions


class PublicStayController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/stays",
            tags=["Public - Stays"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._search_stays, {"response_model": PublicStayListResponseSchema}),
            ("get", "/search", self._search_stays, {"response_model": PublicStayListResponseSchema}),
            ("get", "/{slug}", self._get_stay, {"response_model": PublicStayResponse}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _search_stays(
        self,
        params: PublicSearchStaysQueryDTO = Depends(),
        use_case: PublicSearchStaysUseCase = Depends(public_search_stays_use_case),
    ):
        stays = await use_case.execute(params)
        return self.build_response(
            message="Stays retrieved successfully.",
            data=stays.items,
            meta=self.pagination_meta(stays),
        )

    @handle_api_exceptions
    async def _get_stay(
        self,
        slug: str,
        use_case: PublicGetPropertyUseCase = Depends(public_get_stay_use_case),
    ):
        stay_data = await use_case.execute(slug)
        return self.build_response(
            message="Stay retrieved successfully.",
            data=stay_data,
        )


controller = PublicStayController()
router = controller.router

