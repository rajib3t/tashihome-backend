from fastapi import APIRouter, Depends
from app.api.base_controller import BaseController
from app.application.use_case.admin.settings.get_setting_use_case import GetSettingUseCase
from app.deps.settings import get_get_setting_use_case
from app.schemas.setting_schema import SettingResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PublicSettingsController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/settings",
            tags=["Public - Settings"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_settings, {"response_model": SettingResponseSchema, "response_model_by_alias": False}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_settings(
        self,
        use_case: GetSettingUseCase = Depends(get_get_setting_use_case),
    ):
        result = await use_case.execute()
        return self.build_response(
            "Settings fetched successfully",
            data=result,
        )


controller = PublicSettingsController()
router = controller.router

