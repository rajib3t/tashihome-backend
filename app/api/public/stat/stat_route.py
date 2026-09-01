from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.use_case.public.stat.get_public_stats_use_case import GetPublicStatsUseCase
from app.deps.public.stat import get_public_stats_use_case
from app.schemas.public.stat_schema import PublicStatsResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicStatController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/stats",
            tags=["Public - Stats"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "", self._get_stats, {"response_model": PublicStatsResponseSchema}),
            ("get", "/", self._get_stats, {"response_model": PublicStatsResponseSchema, "include_in_schema": False}),
            ("get", "/overview", self._get_stats, {"response_model": PublicStatsResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_stats(
        self,
        use_case: GetPublicStatsUseCase = Depends(get_public_stats_use_case),
    ):
        data = await use_case.execute()
        return self.build_response(
            message="Public statistics retrieved successfully.",
            data=data,
        )


controller = PublicStatController()
router = controller.router

