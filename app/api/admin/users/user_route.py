from fastapi import APIRouter, Depends, File, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.users.user import (
    UserDTO,
    UserQueryDTO,
    UserResetLinkDTO,
    UserStatusUpdateDTO,
    UserUpdateDTO,
)
from app.application.use_case.admin.users.create_user_use_case import CreateUserUseCase
from app.application.use_case.admin.users.get_user_use_case import GetUserUseCase
from app.application.use_case.admin.users.list_user_use_case import ListUserUseCase
from app.application.use_case.admin.users.send_password_reset_link_use_case import (
    SendUserPasswordResetLinkUseCase,
)
from app.application.use_case.admin.users.update_user_use_case import (
    UpdateStatusUserUseCase,
    UpdateUserUseCase,
    UploadUserProfileImageUseCase,
)
from app.deps.user import (
    get_admin_create_user_use_case,
    get_admin_get_user_use_case,
    get_admin_list_user_use_case,
    get_admin_send_password_reset_link_use_case,
    get_admin_update_user_status_use_case,
    get_admin_update_user_use_case,
    get_admin_upload_user_profile_image_use_case,
)
from app.schemas.user_schema import UserListResponseSchema, UserResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AdminUserController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/users",
            tags=["Admin - Users"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_users, {"response_model": UserListResponseSchema}),
            ("post", "/", self._create_user, {"response_model": UserResponseSchema, "status_code": 201}),
            ("get", "/{user_id}", self._get_user, {"response_model": UserResponseSchema}),
            ("put", "/{user_id}", self._update_user, {"response_model": UserResponseSchema}),
            ("patch", "/{user_id}/status", self._update_user_status_body, {"response_model": UserResponseSchema}),
            ("patch", "/change/{user_id}/{status}", self._update_user_status, {"response_model": UserResponseSchema}),
            ("patch", "/{user_id}/profile-image", self._update_user_profile_image, {"response_model": UserResponseSchema}),
            ("post", "/{user_id}/password-reset", self._send_password_reset_link, {"response_model": None, "status_code": 200}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_users(
        self,
        params: UserQueryDTO = Depends(),
        use_case: ListUserUseCase = Depends(get_admin_list_user_use_case),
    ):
        users_page = await use_case.execute(params)
        return self.build_response(
            message="Users retrieved successfully.",
            data=users_page.items,
            meta=self.pagination_meta(users_page),
        )

    @handle_api_exceptions
    async def _create_user(
        self,
        data: UserDTO,
        use_case: CreateUserUseCase = Depends(get_admin_create_user_use_case),
    ):
        user = await use_case.execute(data)
        return self.build_response(
            message="User created successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _get_user(
        self,
        user_id: str,
        use_case: GetUserUseCase = Depends(get_admin_get_user_use_case),
    ):
        user = await use_case.execute(user_id)
        return self.build_response(
            message="User retrieved successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _update_user(
        self,
        user_id: str,
        data: UserUpdateDTO,
        use_case: UpdateUserUseCase = Depends(get_admin_update_user_use_case),
    ):
        user = await use_case.execute(user_id, data)
        return self.build_response(
            message="User updated successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _update_user_status_body(
        self,
        user_id: str,
        data: UserStatusUpdateDTO,
        use_case: UpdateStatusUserUseCase = Depends(get_admin_update_user_status_use_case),
    ):
        user = await use_case.execute(user_id, data.status)
        return self.build_response(
            message="User status updated successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _update_user_status(
        self,
        user_id: str,
        status: str,
        use_case: UpdateStatusUserUseCase = Depends(get_admin_update_user_status_use_case),
    ):
        user = await use_case.execute(user_id, status)
        return self.build_response(
            message="User status updated successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _update_user_profile_image(
        self,
        user_id: str,
        profile_image: UploadFile = File(...),
        use_case: UploadUserProfileImageUseCase = Depends(get_admin_upload_user_profile_image_use_case),
    ):
        user = await use_case.execute(user_id, profile_image)
        return self.build_response(
            message="User profile image updated successfully.",
            data=user,
        )

    @handle_api_exceptions
    async def _send_password_reset_link(
        self,
        user_id: str,
        data: UserResetLinkDTO,
        use_case: SendUserPasswordResetLinkUseCase = Depends(get_admin_send_password_reset_link_use_case),
    ):
        result = await use_case.execute(user_id, data)
        return self.build_response(
            message=result.get("message", "Password reset link sent successfully."),
            data=None,
        )


controller = AdminUserController()
router = controller.router

