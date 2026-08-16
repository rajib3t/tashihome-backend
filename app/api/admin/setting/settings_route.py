from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, Response
from typing import Optional

from app.api.base_controller import BaseController
from app.application.dto.setting import SettingUpdateDTO
from app.application.use_case.admin.settings.get_setting_use_case import GetSettingUseCase
from app.application.use_case.admin.settings.update_setting_use_case import UpdateSettingUseCase
from app.core.config import settings
from app.deps.settings import get_get_setting_use_case, get_update_setting_use_case
from app.schemas.setting_schema import SettingResponseSchema
import logging
from app.core.csrf import issue_csrf_cookie
from app.services.cloudfront_service import CloudFrontService
from app.utils.exception_decorate import handle_api_exceptions

logger = logging.getLogger(__name__)

class SettingsController(BaseController):
    

    def __init__(self):
        
        

        self.router = APIRouter(
            prefix="/settings",
            tags=["Settings"],
        )
        self._register_routes()

    def _register_routes(self):

        routes = [
            ("post", "/", self._save_setting, {"response_model":SettingResponseSchema , "response_model_by_alias": False}),
            ("get", "/fetch", self._get_settings, {"response_model":SettingResponseSchema , "response_model_by_alias": False}),
        ]


        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async  def _save_setting(
            self,
            app_name: str = Form(...),
            app_logo: Optional[UploadFile] = File(None),
            white_logo: Optional[UploadFile] = File(None),
            app_favicon: Optional[UploadFile] = File(None),
            app_timezone: Optional[str] = Form("Asia/Kolkata"),
            app_date_format:Optional[str] = Form("DD/MM/YYYY"),
            app_time_format: Optional[str] = Form("12h"),
            is_enabled_coming_soon: Optional[bool] = Form(False),
            launch_date:Optional[datetime] = Form(None),
            coming_soon_message: Optional[str] = Form(""),
            coming_background_image: Optional[UploadFile] = File(None),
            coming_soon_video: Optional[UploadFile] = File(None),
            use_case: UpdateSettingUseCase = Depends(get_update_setting_use_case)

        ):
        settings_payload = SettingUpdateDTO(
            app_name=app_name,
            app_logo=app_logo,
            white_logo=white_logo,   
            app_favicon=app_favicon,
            app_timezone=app_timezone,
            app_date_format=app_date_format,
            app_time_format=app_time_format,
            is_enabled_coming_soon=is_enabled_coming_soon,
            launch_date=launch_date,
            coming_soon_message=coming_soon_message,
            coming_background_image=coming_background_image,
            coming_soon_video=coming_soon_video,
        )

        
        result = await use_case.execute(settings_payload)
        return self.build_response(
            "Settings saved successfully",
            data=result
        )

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
        issue_csrf_cookie(response)  # issue CSRF token on successful login
        result = await use_case.execute()
        return self.build_response(
            "Settings fetched successfully",
            data=result,
        )
        
controller = SettingsController()
router = controller.router
