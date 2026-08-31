from fastapi import UploadFile

from app.application.dto.staffs.staff import StaffUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import UserRole, UserStatus
from app.schemas.user_schema import UserData
from app.services.setting_service import SettingNotFoundError
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class UpdateStaffUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, staff_id: str, staff_data: StaffUpdateDTO) -> UserData:
        user = await self.user_service.get_user_by_public_id(public_id=staff_id, flush=True)
        if user is None or user.role not in (UserRole.ADMIN, UserRole.STAFF):
            raise AppException(
                status_code=404,
                message="Staff not found",
                error_code="USER_NOT_FOUND",
                field="staff_id",
            )

        if staff_data.email is not None:
            normalized_email = staff_data.email.strip().lower() if staff_data.email.strip() else None
            if normalized_email:
                duplicate_email = await self.user_service.get_user_by_email(
                    email=normalized_email,
                    flush=False,
                )
                if duplicate_email and duplicate_email.id != user.id:
                    raise AppException(
                        status_code=409,
                        message="Email already exists",
                        error_code="EMAIL_ALREADY_EXISTS",
                        field="email",
                    )
                user.email = normalized_email

        if staff_data.phone is not None:
            phone = staff_data.phone.strip() if staff_data.phone.strip() else None
            if phone:
                duplicate_phone = await self.user_service.get_user_by_phone(
                    phone=phone,
                    flush=False,
                )
                if duplicate_phone and duplicate_phone.id != user.id:
                    raise AppException(
                        status_code=409,
                        message="Phone number already exists",
                        error_code="PHONE_ALREADY_EXISTS",
                        field="phone",
                    )
            user.phone = phone

        if staff_data.full_name is not None:
            user.full_name = staff_data.full_name.strip() if staff_data.full_name.strip() else None

        if staff_data.role is not None:
            role = staff_data.role
            if isinstance(role, str):
                role_val = role.strip().lower()
                if role_val == "admin":
                    role = UserRole.ADMIN
                elif role_val == "staff":
                    role = UserRole.STAFF
                else:
                    raise AppException(
                        status_code=422,
                        message="Role must be 'admin' or 'staff'.",
                        error_code="ROLE_INVALID",
                        field="role",
                    )
            elif role not in (UserRole.ADMIN, UserRole.STAFF):
                raise AppException(
                    status_code=422,
                    message="Role must be 'admin' or 'staff'.",
                    error_code="ROLE_INVALID",
                    field="role",
                )
            user.role = role

        if staff_data.is_subscribed is not None:
            user.is_subscribed = bool(staff_data.is_subscribed)

        updated_user = await self.user_service.update(user, commit=True)

        return UserData(
            id=str(updated_user.public_id),
            email=updated_user.email,
            full_name=updated_user.full_name or "",
            phone=updated_user.phone,
            status=updated_user.status.value if hasattr(updated_user.status, "value") else str(updated_user.status),
            role=updated_user.role,
            is_profile_image_url=updated_user.is_profile_image_url,
            is_subscribed=updated_user.is_subscribed,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )


class UploadStaffProfileImageUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "profile_image_file": {
            "allowed_prefixes": ("image/png", "image/jpeg", "image/jpg"),
            "max_size_bytes": 2 * 1024 * 1024,  # 2 MB
        },
    }

    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(
        self,
        staff_id: str,
        profile_image_file: UploadFile,
    ) -> UserData:
        user = await self.user_service.get_user_by_public_id(public_id=staff_id, flush=True)
        if user is None or user.role not in (UserRole.ADMIN, UserRole.STAFF):
            raise AppException(
                status_code=404,
                message="Staff not found",
                error_code="USER_NOT_FOUND",
                field="staff_id",
            )

        if self._is_upload_file(profile_image_file):
            try:
                old_dp = user.is_profile_image_url
            except SettingNotFoundError:
                old_dp = None
            await self._delete_replaced_file(old_dp, profile_image_file)
            profile_image_key = await self._upload_file(
                profile_image_file,
                folder="user_profiles",
                field_name="profile_image_file",
                webp=True,
            )
            user.is_profile_image_url = profile_image_key

        updated_user = await self.user_service.update(user, commit=True)

        return UserData(
            id=str(updated_user.public_id),
            email=updated_user.email,
            full_name=updated_user.full_name or "",
            phone=updated_user.phone,
            status=updated_user.status.value if hasattr(updated_user.status, "value") else str(updated_user.status),
            role=updated_user.role,
            is_profile_image_url=updated_user.is_profile_image_url,
            is_subscribed=updated_user.is_subscribed,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )


class UpdateStatusStaffUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(self, staff_id: str, status: str) -> UserData:
        user = await self.user_service.get_user_by_public_id(public_id=staff_id, flush=True)
        if user is None or user.role not in (UserRole.ADMIN, UserRole.STAFF):
            raise AppException(
                status_code=404,
                message="Staff not found",
                error_code="USER_NOT_FOUND",
                field="staff_id",
            )

        normalized_status = status.strip().lower()
        if normalized_status not in ["active", "inactive", "suspended"]:
            raise AppException(
                status_code=422,
                message="Status must be 'active', 'inactive', or 'suspended'.",
                field="status",
                error_code="STATUS_INVALID",
            )

        if normalized_status == "active":
            user.status = UserStatus.ACTIVE
        elif normalized_status == "inactive":
            user.status = UserStatus.INACTIVE
        elif normalized_status == "suspended":
            user.status = UserStatus.SUSPENDED

        updated_user = await self.user_service.update(user, commit=True)

        return UserData(
            id=str(updated_user.public_id),
            email=updated_user.email,
            full_name=updated_user.full_name or "",
            phone=updated_user.phone,
            status=updated_user.status.value if hasattr(updated_user.status, "value") else str(updated_user.status),
            role=updated_user.role,
            is_profile_image_url=updated_user.is_profile_image_url,
            is_subscribed=updated_user.is_subscribed,
            created_at=updated_user.created_at,
            updated_at=updated_user.updated_at,
        )

