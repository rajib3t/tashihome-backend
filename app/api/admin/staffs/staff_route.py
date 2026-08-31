from fastapi import APIRouter, Depends, File, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.staffs.staff import (
    StaffDTO,
    StaffQueryDTO,
    StaffResetLinkDTO,
    StaffStatusUpdateDTO,
    StaffUpdateDTO,
)
from app.application.use_case.admin.staffs.create_staff_use_case import CreateStaffUseCase
from app.application.use_case.admin.staffs.get_staff_use_case import GetStaffUseCase
from app.application.use_case.admin.staffs.list_staff_use_case import ListStaffUseCase
from app.application.use_case.admin.staffs.send_password_reset_link_use_case import (
    SendStaffPasswordResetLinkUseCase,
)
from app.application.use_case.admin.staffs.update_staff_use_case import (
    UpdateStaffUseCase,
    UpdateStatusStaffUseCase,
    UploadStaffProfileImageUseCase,
)
from app.deps.auth import require_admin
from app.deps.staff import (
    get_admin_create_staff_use_case,
    get_admin_get_staff_use_case,
    get_admin_list_staff_use_case,
    get_admin_send_staff_password_reset_link_use_case,
    get_admin_update_staff_status_use_case,
    get_admin_update_staff_use_case,
    get_admin_upload_staff_profile_image_use_case,
)
from app.schemas.user_schema import UserListResponseSchema, UserResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class AdminStaffController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/staffs",
            tags=["Admin - Staffs"],
            dependencies=[Depends(require_admin)],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_staffs, {"response_model": UserListResponseSchema}),
            ("post", "/", self._create_staff, {"response_model": UserResponseSchema, "status_code": 201}),
            ("get", "/{staff_id}", self._get_staff, {"response_model": UserResponseSchema}),
            ("put", "/{staff_id}", self._update_staff, {"response_model": UserResponseSchema}),
            ("patch", "/{staff_id}/status", self._update_staff_status_body, {"response_model": UserResponseSchema}),
            ("patch", "/change/{staff_id}/{status}", self._update_staff_status, {"response_model": UserResponseSchema}),
            ("patch", "/{staff_id}/profile-image", self._update_staff_profile_image, {"response_model": UserResponseSchema}),
            ("post", "/{staff_id}/password-reset", self._send_password_reset_link, {"response_model": None, "status_code": 200}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_staffs(
        self,
        params: StaffQueryDTO = Depends(),
        use_case: ListStaffUseCase = Depends(get_admin_list_staff_use_case),
    ):
        staffs_page = await use_case.execute(params)
        return self.build_response(
            message="Staff members retrieved successfully.",
            data=staffs_page.items,
            meta=self.pagination_meta(staffs_page),
        )

    @handle_api_exceptions
    async def _create_staff(
        self,
        data: StaffDTO,
        use_case: CreateStaffUseCase = Depends(get_admin_create_staff_use_case),
    ):
        staff = await use_case.execute(data)
        return self.build_response(
            message="Staff member created successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _get_staff(
        self,
        staff_id: str,
        use_case: GetStaffUseCase = Depends(get_admin_get_staff_use_case),
    ):
        staff = await use_case.execute(staff_id)
        return self.build_response(
            message="Staff member retrieved successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _update_staff(
        self,
        staff_id: str,
        data: StaffUpdateDTO,
        use_case: UpdateStaffUseCase = Depends(get_admin_update_staff_use_case),
    ):
        staff = await use_case.execute(staff_id, data)
        return self.build_response(
            message="Staff member updated successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _update_staff_status_body(
        self,
        staff_id: str,
        data: StaffStatusUpdateDTO,
        use_case: UpdateStatusStaffUseCase = Depends(get_admin_update_staff_status_use_case),
    ):
        staff = await use_case.execute(staff_id, data.status)
        return self.build_response(
            message="Staff status updated successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _update_staff_status(
        self,
        staff_id: str,
        status: str,
        use_case: UpdateStatusStaffUseCase = Depends(get_admin_update_staff_status_use_case),
    ):
        staff = await use_case.execute(staff_id, status)
        return self.build_response(
            message="Staff status updated successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _update_staff_profile_image(
        self,
        staff_id: str,
        profile_image: UploadFile = File(...),
        use_case: UploadStaffProfileImageUseCase = Depends(get_admin_upload_staff_profile_image_use_case),
    ):
        staff = await use_case.execute(staff_id, profile_image)
        return self.build_response(
            message="Staff profile image updated successfully.",
            data=staff,
        )

    @handle_api_exceptions
    async def _send_password_reset_link(
        self,
        staff_id: str,
        data: StaffResetLinkDTO,
        use_case: SendStaffPasswordResetLinkUseCase = Depends(get_admin_send_staff_password_reset_link_use_case),
    ):
        result = await use_case.execute(staff_id, data)
        return self.build_response(
            message=result.get("message", "Password reset link sent successfully."),
            data=None,
        )


controller = AdminStaffController()
router = controller.router

