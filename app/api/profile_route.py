from fastapi import APIRouter, Depends, File, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.profile import UpdatePasswordDTO, UpdateProfileInfoDTO
from app.application.use_case.user.profile_use_case import ProfileUseCase
from app.application.use_case.user.update_password_use_case import UpdatePasswordUseCase
from app.application.use_case.user.update_profile_image_use_case import UpdateProfileImageUseCase
from app.application.use_case.user.update_profile_info_use_case import UpdateProfileInfoUseCase
from app.core.csrf import verify_csrf
from app.deps.user import (
    get_update_password_use_case,
    get_update_profile_image_use_case,
    get_update_profile_info_use_case,
    get_user_profile_use_case,
)
from app.schemas.user_schema import UserBasicProfileResponse
from app.utils.exception_decorate import handle_api_exceptions


class ProfileController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/profile",
            tags=["User - Profile"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            (
                "get",
                "/",
                self._get_profile,
                {"response_model": UserBasicProfileResponse, "response_model_by_alias": False},
            ),
            (
                "put",
                "/info",
                self._update_profile_info,
                {
                    "response_model": UserBasicProfileResponse,
                    "response_model_by_alias": False,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "put",
                "/password",
                self._update_password,
                {
                    "response_model": UserBasicProfileResponse,
                    "response_model_by_alias": False,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "post",
                "/image",
                self._update_profile_image,
                {
                    "response_model": UserBasicProfileResponse,
                    "response_model_by_alias": False,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
            (
                "delete",
                "/image",
                self._delete_profile_image,
                {
                    "response_model": UserBasicProfileResponse,
                    "response_model_by_alias": False,
                    "dependencies": [Depends(verify_csrf)],
                },
            ),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_profile(
        self,
        use_case: ProfileUseCase = Depends(get_user_profile_use_case),
    ):
        result = await use_case.execute()
        return self.build_response(
            message="Profile retrieved successfully",
            data=result,
        )

    @handle_api_exceptions
    async def _update_profile_info(
        self,
        data: UpdateProfileInfoDTO,
        use_case: UpdateProfileInfoUseCase = Depends(get_update_profile_info_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Profile information updated successfully",
            data=result,
        )

    @handle_api_exceptions
    async def _update_password(
        self,
        data: UpdatePasswordDTO,
        use_case: UpdatePasswordUseCase = Depends(get_update_password_use_case),
    ):
        result = await use_case.execute(data)
        return self.build_response(
            message="Password updated successfully",
            data=result,
        )

    @handle_api_exceptions
    async def _update_profile_image(
        self,
        profile_image: UploadFile = File(...),
        use_case: UpdateProfileImageUseCase = Depends(get_update_profile_image_use_case),
    ):
        result = await use_case.execute(profile_image)
        return self.build_response(
            message="Profile image updated successfully",
            data=result,
        )

    @handle_api_exceptions
    async def _delete_profile_image(
        self,
        use_case: UpdateProfileImageUseCase = Depends(get_update_profile_image_use_case),
    ):
        result = await use_case.delete_image()
        return self.build_response(
            message="Profile image removed successfully",
            data=result,
        )


controller = ProfileController()
router = controller.router
