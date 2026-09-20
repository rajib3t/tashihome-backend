from fastapi import APIRouter, Depends, Response
from app.api.base_controller import BaseController
from app.application.use_case.admin.settings.get_setting_use_case import GetSettingUseCase
from app.deps.settings import get_get_setting_use_case
from app.schemas.setting_schema import SettingResponseSchema
from app.utils.exception_decorate import handle_api_exceptions
from app.core.config import settings
from app.services.cloudfront_service import CloudFrontService
import logging
logger = logging.getLogger(__name__)

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
        response: Response,
        use_case: GetSettingUseCase = Depends(get_get_setting_use_case),
        
    ):
        if (
                    settings.CLOUDFRONT_DOMAIN
                    and settings.CLOUDFRONT_KEY_PAIR_ID
                    and settings.CLOUDFRONT_PRIVATE_KEY_PATH
                ):
                    cloudfront_service = CloudFrontService(
                        domain=settings.CLOUDFRONT_DOMAIN,
                        key_pair_id=settings.CLOUDFRONT_KEY_PAIR_ID,
                        private_key_path=settings.CLOUDFRONT_PRIVATE_KEY_PATH,
                        cookie_ttl=settings.CLOUDFRONT_COOKIE_TTL or 3600,
                    )
                    cookies = cloudfront_service.create_signed_cookies()
                    for name, value in cookies.items():
                        response.set_cookie(
                            key=name,
                            value=value,
                            domain=settings.CLOUDFRONT_COOKIE_DOMAIN,
                            secure=settings.SECURE_COOKIES,
                            httponly=True,
                            samesite=settings.cookie_samesite,
                            max_age=settings.CLOUDFRONT_COOKIE_TTL or 3600,
                            path="/",
                        )
        else:
            logger.info("CloudFront signing skipped because configuration is incomplete")
        result = await use_case.execute(is_admin=False)
        return self.build_response(
            "Settings fetched successfully",
            data=result,
        )


controller = PublicSettingsController()
router = controller.router

