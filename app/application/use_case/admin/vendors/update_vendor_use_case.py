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

            # Fix #1: only look up duplicates when the field is actually being updated,
            # otherwise vendor_data.email / vendor_data.phone may be None and this
            # would raise (e.g. AttributeError on None.lower()).
            normalized_email = None
            if vendor_data.email is not None:
                normalized_email = empty_to_none(vendor_data.email)
                if normalized_email is None:
                    normalized_email = None
                else:
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
            # Fix #2: store the same normalized (lowercased) value that was
            # checked for duplicates above, so case-variant duplicates can't slip in.
            vendor.email = normalized_email
        phone = empty_to_none(vendor_data.phone)
        if phone is not None:
            vendor.phone = phone

        # Update the vendor's information within the same transaction.
        # Update the vendor's information within the same transaction.
        if vendor_data.company is not None:
            company_name = empty_to_none(vendor_data.company.name)
            company_email = empty_to_none(vendor_data.company.email)
            company_phone = empty_to_none(vendor_data.company.phone)
            has_company_update = any([company_name, company_email, company_phone, vendor_data.company.address is not None])

            if vendor.company is None:
                if not has_company_update:
                    vendor_data.company = None
                    has_company_update = False
                else:
                    company = Company(
                        name=company_name or "",
                        email=company_email or "",
                        phone=company_phone,
                        user_id=vendor.id,
                    )
                    await self.company_service.create(company, commit=False)
                    vendor.company = company
            elif any([company_name is not None, company_email is not None, company_phone is not None]):
                if company_name is not None:
                    vendor.company.name = company_name
                if company_email is not None:
                    vendor.company.email = company_email
                if company_phone is not None:
                    vendor.company.phone = company_phone
                await self.company_service.update(vendor.company, commit=False)

            # Handle address update if provided.
            if vendor_data.company.address is not None and vendor.company is not None:
                address_line1 = empty_to_none(vendor_data.company.address.address_line1)
                address_line2 = empty_to_none(vendor_data.company.address.address_line2)
                postal_code = empty_to_none(vendor_data.company.address.postal_code)
                country = empty_to_none(vendor_data.company.address.country)
                if any([address_line1, address_line2, postal_code, country]):
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

        # These must run regardless of whether a company payload was sent.
        updated_vendor = await self.user_service.update(
            vendor,
            with_relations={"company": True},
            commit=False,
        )

        await session.flush()

        if updated_vendor.is_profile_image_url:
            updated_vendor.is_profile_image_url = self.storage_service.generate_presigned_url(
                updated_vendor.is_profile_image_url,
            )

        
        return await self.user_service.build_vendor_response(updated_vendor)


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
