from fastapi import UploadFile

from app.application.dto.vendors.vendor import VendorDTO, VendorUpdateDTO, VendorCompanyUpdateDTO, VendorAddressUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.user_model import User
from app.deps.auth import CurrentUser
from app.repositories.address_repository import AddressRepository
from app.repositories.company_repository import CompanyRepository
from app.schemas.vendor_schema import VendorAddressData, VendorCompanyData, VendorUserResponseData
from app.services.address_service import AddressService
from app.services.company_service import CompanyService
from app.services.setting_service import SettingNotFoundError
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class UpdateVendorUseCase(BaseUseCase):
    def __init__(
        self,
        user_service: UserService,
        storage_service: StorageService,
        company_service: CompanyService,
        address_service: AddressService,
        verify_csrf: bool,
        current_user: CurrentUser,
    ):
        self.user_service = user_service
        self.storage_service = storage_service
        self.company_service = company_service
        self.address_service = address_service
        self.verify_csrf = verify_csrf
        self.current_user = current_user

    async def execute(
        self,
        user_id: str,
        vendor_data: VendorUpdateDTO,
    ) -> User:
        def empty_to_none(value: str | None) -> str | None:
            if value is None:
                return None
            stripped = value.strip()
            return stripped if stripped else None

        def has_meaningful_value(value: str | None) -> bool:
            return value is not None and value.strip() != ""

        def has_meaningful_company_fields(company_data: VendorCompanyUpdateDTO | None) -> bool:
            if company_data is None:
                return False

            company_values = [
                empty_to_none(company_data.name),
                empty_to_none(company_data.email),
                empty_to_none(company_data.phone),
            ]

            address = company_data.address
            if address is not None:
                company_values.extend([
                    empty_to_none(address.address_line1),
                    empty_to_none(address.address_line2),
                    empty_to_none(address.postal_code),
                    empty_to_none(address.country),
                ])

            return any(has_meaningful_value(value) for value in company_values)

        session = self.user_service.user_repository.db
        tx = session.begin_nested() if session.in_transaction() else session.begin()

        async with tx:
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

            if vendor.role != "vendor":
                raise AppException(
                    status_code=400,
                    message="User is not a vendor",
                    error_code="USER_NOT_VENDOR",
                    field="vendor_id",
                )

            normalized_email = None
            if vendor_data.email is not None:
                normalized_email = empty_to_none(vendor_data.email)
                if normalized_email is not None:
                    normalized_email = normalized_email.lower()
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

            full_name = empty_to_none(vendor_data.full_name)
            if full_name is not None:
                vendor.full_name = full_name
            if vendor_data.email is not None:
                vendor.email = normalized_email
            phone = empty_to_none(vendor_data.phone)
            if phone is not None:
                vendor.phone = phone

            if vendor_data.company is not None:
                company_name = empty_to_none(vendor_data.company.name)
                company_email = empty_to_none(vendor_data.company.email)
                company_phone = empty_to_none(vendor_data.company.phone)
                address_line1 = empty_to_none(vendor_data.company.address.address_line1) if vendor_data.company.address is not None else None
                address_line2 = empty_to_none(vendor_data.company.address.address_line2) if vendor_data.company.address is not None else None
                postal_code = empty_to_none(vendor_data.company.address.postal_code) if vendor_data.company.address is not None else None
                country = empty_to_none(vendor_data.company.address.country) if vendor_data.company.address is not None else None
                has_company_update = has_meaningful_company_fields(vendor_data.company)

                if not has_company_update:
                    vendor_data.company = None
                elif vendor.company is None:
                    company = Company(
                        name=company_name or "",
                        email=company_email or "",
                        phone=company_phone,
                        user_id=vendor.id,
                    )
                    await self.company_service.create(company, commit=False)
                    vendor.company = company
                else:
                    if company_name is not None:
                        vendor.company.name = company_name
                    if company_email is not None:
                        vendor.company.email = company_email
                    if company_phone is not None:
                        vendor.company.phone = company_phone
                    await self.company_service.update(vendor.company, commit=False)

                if vendor_data.company is not None and vendor.company is not None:
                    if any([
                        has_meaningful_value(address_line1),
                        has_meaningful_value(address_line2),
                        has_meaningful_value(postal_code),
                        has_meaningful_value(country),
                    ]):
                        company_id = vendor.company.id
                        if company_id is None:
                            await session.flush()
                            company_id = vendor.company.id

                        address = await self.address_service.get_company_address_by_owner_id(
                            owner_id=company_id,
                            flush=False,
                        )
                        if address is None:
                            address = Address(
                                address_line1=address_line1 or "",
                                address_line2=address_line2,
                                postal_code=postal_code or "",
                                country=country or "",
                                owner_id=company_id,
                                owner_type="company",
                            )
                            await self.address_service.create(address, commit=False)
                        else:
                            if address_line1 is not None:
                                address.address_line1 = address_line1
                            if address_line2 is not None:
                                address.address_line2 = address_line2
                            if postal_code is not None:
                                address.postal_code = postal_code
                            if country is not None:
                                address.country = country
                            await self.address_service.update(address, commit=False)

            updated_vendor = await self.user_service.update(
                vendor,
                with_relations={"company": True},
                commit=False,
            )
            await session.flush()

            profile_image_url = self.storage_service.get_display_url(
                updated_vendor.is_profile_image_url
            )
            return await self.user_service.build_vendor_response(
                updated_vendor,
                profile_image_url=profile_image_url,
            )


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
    ) -> VendorUserResponseData:
       
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

        # Upload the profile image to S3 and get the URL
        if self._is_upload_file(profile_image_file):
            try:
                old_dp  = vendor.is_profile_image_url
            except SettingNotFoundError:
                old_dp = None
            await self._delete_replaced_file(old_dp, profile_image_file)
            profile_image_key = await self._upload_file(
                profile_image_file, folder="vendor_profiles", field_name="profile_image_file", webp =True
            )

            vendor.is_profile_image_url = profile_image_key

        data = await self.user_service.update(
            vendor,
            commit=True,
        )

        profile_image_url = (
            self.storage_service.get_display_url(data.is_profile_image_url)
            if data.is_profile_image_url
            else None
        )

        return await self.user_service.build_vendor_response(
            data,
            profile_image_url=profile_image_url,
        )
