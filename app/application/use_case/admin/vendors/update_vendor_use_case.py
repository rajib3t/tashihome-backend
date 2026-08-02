from fastapi import UploadFile

from app.application.dto.vendors.vendor import VendorUpdateDTO
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
        company_service: UserService,
        address_service: UserService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.company_service = company_service
        self.address_service = address_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(
        self,
        user_id: str,
        vendor_data: VendorUpdateDTO,
    ) -> VendorUserResponseData:
        db = self.user_service.user_repository.db
        vendor = await self._validate_vendor_update(user_id, vendor_data)

        try:
            vendor = await self.user_service.update_vendor_profile(user_id, vendor_data)

            company_payload = vendor_data.company
            if company_payload is not None:
                company = vendor.company
                if company is None:
                    company = Company(
                        user_id=vendor.id,
                        name=company_payload.name or vendor.full_name or vendor.email,
                        email=company_payload.email or vendor.email,
                        phone=company_payload.phone or vendor.phone,
                    )
                    await self.user_service.company_service.create_vendor_company(
                        company,
                        commit=False,
                    )
                    await db.flush()
                    await self.user_service.attach_vendor_company(vendor, company)
                else:
                    await self.user_service.company_service.update_vendor_company(
                        company,
                        name=company_payload.name,
                        email=company_payload.email,
                        phone=company_payload.phone,
                    )

                if company_payload.address is not None:
                    address = await self.user_service.address_service.get_company_address_by_owner_id(
                        company.id,
                        flush=True,
                    )
                    if address is None:
                        address = Address(
                            owner_type="company",
                            owner_id=company.id,
                            address_line1=company_payload.address.address_line1 or "",
                            address_line2=company_payload.address.address_line2,
                            postal_code=company_payload.address.postal_code or "",
                            country=company_payload.address.country or "",
                        )
                        await self.user_service.address_service.create_address(
                            address,
                            commit=False,
                        )
                    else:
                        await self.user_service.address_service.update_company_address(
                            address,
                            address_line1=company_payload.address.address_line1,
                            address_line2=company_payload.address.address_line2,
                            postal_code=company_payload.address.postal_code,
                            country=company_payload.address.country,
                        )
                        await self.user_service.address_service.persist_company_address(
                            address,
                            commit=False,
                        )

            await db.commit()
            return await self.user_service.build_vendor_response(vendor)
        except Exception:
            await db.rollback()
            raise

    async def _validate_vendor_update(self, user_id: str, vendor_data: VendorUpdateDTO) -> User:
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

        if vendor_data.email is not None:
            existing_user = await self.user_service.get_user_by_email(
                vendor_data.email,
                with_relations=None,
                flush=True,
            )
            if existing_user is not None and existing_user.id != vendor.id:
                raise AppException(
                    status_code=409,
                    message="User email already exists",
                    error_code="USER_EMAIL_EXISTS",
                    field="email",
                )

            if vendor.company is not None:
                existing_company_email = await self.user_service.company_service.get_by_email(vendor_data.email, flush=True)
                if existing_company_email is not None and existing_company_email.id != vendor.company.id:
                    raise AppException(
                        status_code=409,
                        message="Company email already exists",
                        error_code="COMPANY_EMAIL_EXISTS",
                        field="company.email",
                    )

        if vendor_data.phone is not None:
            existing_user_phone = await self.user_service.get_user_by_phone(vendor_data.phone, flush=True)
            if existing_user_phone is not None and existing_user_phone.id != vendor.id:
                raise AppException(
                    status_code=409,
                    message="User phone already exists",
                    error_code="USER_PHONE_EXISTS",
                    field="phone",
                )

        if vendor_data.company is not None:
            company_payload = vendor_data.company
            if company_payload.email is not None:
                existing_company_email = await self.user_service.company_service.get_by_email(company_payload.email, flush=True)
                if existing_company_email is not None:
                    if vendor.company is None or existing_company_email.id != vendor.company.id:
                        raise AppException(
                            status_code=409,
                            message="Company email already exists",
                            error_code="COMPANY_EMAIL_EXISTS",
                            field="company.email",
                        )

            if company_payload.name is not None:
                existing_company_name = await self.user_service.company_service.get_by_name(company_payload.name, flush=True)
                if existing_company_name is not None:
                    if vendor.company is None or existing_company_name.id != vendor.company.id:
                        raise AppException(
                            status_code=409,
                            message="Company name already exists",
                            error_code="COMPANY_NAME_EXISTS",
                            field="company.name",
                        )

        return vendor




class UploadVendorProfileImageUseCase(BaseUseCase):
    FILE_UPLOAD_RULES = {
        "profile_image_file": {
            "allowed_prefixes": ("image/",),
            "max_size_bytes": 2 * 1024 * 1024,  # 2 MB  2 MB
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

        # Upload the profile image to S3 and get the URL
        if self._is_upload_file(profile_image_file):
            try:
                old_dp  = vendor.is_profile_image_url
            except SettingNotFoundError:
                old_dp = None
            await self._delete_replaced_file(old_dp, profile_image_file)
            profile_image_url = await self._upload_file(
                profile_image_file, folder="vendor_profiles", field_name="profile_image", webp =True
            )

            vendor.is_profile_image_url = profile_image_url

        data = await self.user_service.update(
            vendor,
            commit=True,
        )


        updated_vendor = await self.user_service.get_user_by_public_id(
            public_id=user_id,
            with_relations={"company": True},
            flush=True,
        )

        if updated_vendor.is_profile_image_url:
            updated_vendor.is_profile_image_url = self.storage_service.generate_presigned_url(
                updated_vendor.is_profile_image_url,
            )
        

        return updated_vendor