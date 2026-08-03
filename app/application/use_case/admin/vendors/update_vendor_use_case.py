from fastapi import UploadFile

from app.application.dto.vendors.vendor import VendorDTO, VendorUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.user_model import User
from app.deps.auth import CurrentUser
from app.schemas.vendor_schema import VendorAddressData, VendorCompanyData, VendorUserResponseData
from app.services.setting_service import SettingNotFoundError
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class UpdateVendorUseCase(BaseUseCase):
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
        user_id: str,
        vendor_data: VendorDTO,
    ) -> User:
        vendor = await self.user_service.get_user_by_public_id(
            public_id=user_id,
            with_relations=None,
            flush=True,
        )
        if vendor is None:
            raise AppException(
                status_code=404,
                message="Vendor not found",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        if vendor.role != "vendor":
            raise AppException(
                status_code=400,
                message="User is not a vendor",
                error_code="USER_NOT_VENDOR",
                field="vendor_id",
            )

        # Fix #1: only look up duplicates when the field is actually being updated,
        # otherwise vendor_data.email / vendor_data.phone may be None and this
        # would raise (e.g. AttributeError on None.lower()).
        if vendor_data.email is not None:
            normalized_email = vendor_data.email.lower()
            duplicate_email = await self.user_service.get_user_by_email(
                email=normalized_email,
                with_relations=None,
                flush=False,
            )
            if duplicate_email and duplicate_email.id != vendor.id:
                raise AppException(
                    status_code=409,
                    message="Email already exists",
                    error_code="EMAIL_ALREADY_EXISTS",
                    field="email",
                )

        if vendor_data.phone is not None:
            duplicate_phone = await self.user_service.get_user_by_phone(
                phone=vendor_data.phone,
                with_relations=None,
                flush=False,
            )
            if duplicate_phone and duplicate_phone.id != vendor.id:
                raise AppException(
                    status_code=409,
                    message="Phone number already exists",
                    error_code="PHONE_ALREADY_EXISTS",
                    field="phone",
                )

        if vendor_data.full_name is not None:
            vendor.full_name = vendor_data.full_name
        if vendor_data.email is not None:
            # Fix #2: store the same normalized (lowercased) value that was
            # checked for duplicates above, so case-variant duplicates can't slip in.
            vendor.email = normalized_email
        if vendor_data.phone is not None:
            vendor.phone = vendor_data.phone

        # Update the vendor's information
        updated_vendor = await self.user_service.update(
            vendor,
            with_relations={"company": True},
            commit=True
        )

       
        updated_vendor.is_profile_image_url = self.storage_service.generate_presigned_url(
            updated_vendor.is_profile_image_url,
        )
        return updated_vendor


class UploadVendorProfileImageUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "profile_image_file": {
            "allowed_prefixes": ("image/",),
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
        user_id: str,
        profile_image_file: UploadFile,
    ) -> User:
        vendor = await self.user_service.get_user_by_public_id(
            public_id=user_id,
            with_relations={"company": True},
            flush=True,
        )
        if vendor is None:
            raise AppException(
                status_code=404,
                message="Vendor not found",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        old_dp = getattr(vendor, "is_profile_image_url", None)

        if self._is_upload_file(profile_image_file):
            uploaded_key = None
            try:
                uploaded_key = await self._upload_file(
                    profile_image_file,
                    folder="vendor_profiles",
                    field_name="profile_image_file",
                    webp =True,
                )
                vendor.is_profile_image_url = uploaded_key
                updated_vendor = await self.user_service.update(
                    vendor,
                    with_relations={"company": True},
                    commit=True,
                )
            except Exception:
                if uploaded_key:
                    try:
                        await self.storage_service.delete_object(uploaded_key)
                    except Exception:
                        pass
                vendor.is_profile_image_url = old_dp
                raise

            if old_dp and old_dp != uploaded_key:
                try:
                    await self.storage_service.delete_object(old_dp)
                except Exception:
                    pass

            if updated_vendor.is_profile_image_url:
                updated_vendor.is_profile_image_url = self.storage_service.generate_presigned_url(
                    updated_vendor.is_profile_image_url,
                )
            return updated_vendor

        updated_vendor = await self.user_service.update(
            vendor,
            with_relations={"company": True},
            commit=True,
        )

        if updated_vendor.is_profile_image_url:
            updated_vendor.is_profile_image_url = self.storage_service.generate_presigned_url(
                updated_vendor.is_profile_image_url,
            )

        return updated_vendor
