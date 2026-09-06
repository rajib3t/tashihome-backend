from datetime import datetime
from typing import Optional, Union
import logging

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.setting import SettingUpdateDTO
from app.application.use_case.admin.settings.get_setting_use_case import GetSettingUseCase
from app.application.use_case.admin.settings.update_setting_use_case import UpdateSettingUseCase
from app.core.config import settings
from app.core.csrf import issue_csrf_cookie
from app.deps.settings import get_get_setting_use_case, get_update_setting_use_case
from app.schemas.setting_schema import SettingResponseSchema
from app.services.cloudfront_service import CloudFrontService
from app.utils.exception_decorate import handle_api_exceptions

logger = logging.getLogger(__name__)


class SettingsController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/settings",
            tags=["Admin - Settings"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("post", "/", self._save_setting, {"response_model": SettingResponseSchema, "response_model_by_alias": False}),
            ("get", "/fetch", self._get_settings, {"response_model": SettingResponseSchema, "response_model_by_alias": False}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _save_setting(
        self,
        # Branding & General
        app_name: Optional[str] = Form(None),
        app_logo: Optional[UploadFile] = File(None),
        white_logo: Optional[UploadFile] = File(None),
        app_favicon: Optional[UploadFile] = File(None),
        app_timezone: Optional[str] = Form(None),
        app_date_format: Optional[str] = Form(None),
        app_time_format: Optional[str] = Form(None),
        default_currency: Optional[str] = Form(None),
        currency_symbol: Optional[str] = Form(None),
        # Contact & Support
        contact_email: Optional[str] = Form(None),
        contact_phone: Optional[str] = Form(None),
        contact_address: Optional[str] = Form(None),
        # Booking & Finance Defaults
        default_commission_percentage: Optional[float] = Form(None),
        service_fee_percentage: Optional[float] = Form(None),
        check_in_time: Optional[str] = Form(None),
        check_out_time: Optional[str] = Form(None),
        min_booking_days: Optional[int] = Form(None),
        max_booking_days: Optional[int] = Form(None),
        cancellation_grace_period_hours: Optional[int] = Form(None),
        # Social links
        facebook_url: Optional[str] = Form(None),
        instagram_url: Optional[str] = Form(None),
        twitter_url: Optional[str] = Form(None),
        linkedin_url: Optional[str] = Form(None),
        youtube_url: Optional[str] = Form(None),
        # SEO & Policies
        meta_title: Optional[str] = Form(None),
        meta_description: Optional[str] = Form(None),
        meta_keywords: Optional[str] = Form(None),
        terms_and_conditions_url: Optional[str] = Form(None),
        privacy_policy_url: Optional[str] = Form(None),
        refund_policy_url: Optional[str] = Form(None),
        # Coming Soon
        is_enabled_coming_soon: Optional[bool] = Form(None),
        launch_date: Optional[datetime] = Form(None),
        coming_soon_message: Optional[str] = Form(None),
        coming_background_image: Optional[UploadFile] = File(None),
        coming_soon_video: Optional[UploadFile] = File(None),
        use_case: UpdateSettingUseCase = Depends(get_update_setting_use_case),
    ):
        settings_payload = SettingUpdateDTO(
            app_name=app_name,
            app_logo=app_logo,
            white_logo=white_logo,
            app_favicon=app_favicon,
            app_timezone=app_timezone,
            app_date_format=app_date_format,
            app_time_format=app_time_format,
            default_currency=default_currency,
            currency_symbol=currency_symbol,
            contact_email=contact_email,
            contact_phone=contact_phone,
            contact_address=contact_address,
            default_commission_percentage=default_commission_percentage,
            service_fee_percentage=service_fee_percentage,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            min_booking_days=min_booking_days,
            max_booking_days=max_booking_days,
            cancellation_grace_period_hours=cancellation_grace_period_hours,
            facebook_url=facebook_url,
            instagram_url=instagram_url,
            twitter_url=twitter_url,
            linkedin_url=linkedin_url,
            youtube_url=youtube_url,
            meta_title=meta_title,
            meta_description=meta_description,
            meta_keywords=meta_keywords,
            terms_and_conditions_url=terms_and_conditions_url,
            privacy_policy_url=privacy_policy_url,
            refund_policy_url=refund_policy_url,
            is_enabled_coming_soon=is_enabled_coming_soon,
            launch_date=launch_date,
            coming_soon_message=coming_soon_message,
            coming_background_image=coming_background_image,
            coming_soon_video=coming_soon_video,
        )

        result = await use_case.execute(settings_payload)
        return self.build_response("Settings saved successfully", data=result)

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
        issue_csrf_cookie(response)
        result = await use_case.execute()
        return self.build_response(
            "Settings fetched successfully",
            data=result,
        )


controller = SettingsController()
router = controller.router
