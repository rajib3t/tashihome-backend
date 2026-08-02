from typing import Optional

from app.application.dto.vendors.vendor import VendorUpdateDTO
from app.core.exceptions import AppException
from app.models.address_model import Address
from app.models.company_model import Company
from app.models.user_model import User
from app.models.user_model import UserRole
from app.repositories.user_repository import UserRepository, WithRelations
from app.schemas.vendor_schema import VendorAddressData, VendorCompanyData, VendorUserResponseData
from app.services.address_service import AddressService
from app.services.company_service import CompanyService


class UserService:

    def __init__(
            self, 
            user_repository: UserRepository,
            company_service: CompanyService,
            address_service: AddressService,
        ):
        self.user_repository = user_repository
        self.company_service = company_service
        self.address_service = address_service

    async def get_user_by_email(
            self, 
            email: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[User]:
        # This method retrieves a user by their email address, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_email(
            email, 
            with_relations=with_relations, 
            flush=flush
        )

    async def get_user_by_public_id(
            self, 
            public_id: str, 
            with_relations: Optional[WithRelations] = None, 
            flush: bool = False
        ) -> Optional[User]:
        # This method retrieves a user by their public ID, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_public_id(
            public_id, 
            with_relations=with_relations, 
            flush=flush
        )

    async def get_user_by_id(
        self,
        user_id: int,
        with_relations: Optional[WithRelations] = None, 
        flush: bool = False
    ) -> Optional[User]:
        # This method retrieves a user by their ID, optionally including related data and controlling whether to flush the session.
        return await self.user_repository.get_by_id(
            user_id, 
            with_relations=with_relations, 
            flush=flush
        )

    async def create_user(self, user: User, commit: bool = True) -> User:
        # This method creates a new user in the database.
        return await self.user_repository.create(user, with_relations=None, commit=commit)

    async def get_user_by_phone(
        self,
        phone: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[User]:
        return await self.user_repository.get_by_phone(
            phone,
            with_relations=with_relations,
            flush=flush,
        )

    async def update_vendor_profile(
        self,
        public_id: str,
        vendor_data: VendorUpdateDTO,
    ) -> User:
        vendor = await self.get_user_by_public_id(
            public_id=public_id,
            with_relations={"company": True},
            flush=True,
        )
        if not vendor or vendor.role != UserRole.VENDOR:
            raise AppException(
                status_code=404,
                message="Vendor not found",
                error_code="VENDOR_NOT_FOUND",
                field="vendor_id",
            )

        if vendor_data.full_name is not None:
            vendor.full_name = vendor_data.full_name
        if vendor_data.email is not None:
            vendor.email = vendor_data.email
        if vendor_data.phone is not None:
            vendor.phone = vendor_data.phone

        return vendor

    async def attach_vendor_company(self, vendor: User, company: Company) -> Company:
        vendor.company = company
        return company

    async def build_vendor_response(self, vendor: User) -> VendorUserResponseData:
        refreshed_company = None
        if vendor.company is not None:
            company = vendor.company
            address = await self.address_service.get_company_address_by_owner_id(company.id, flush=True)
            refreshed_address = None
            if address is not None:
                refreshed_address = VendorAddressData(
                    id=str(address.id),
                    address_line1=address.address_line1,
                    address_line2=address.address_line2,
                    postal_code=address.postal_code,
                    country=address.country,
                )
            refreshed_company = VendorCompanyData(
                id=str(company.id),
                name=company.name,
                email=company.email,
                phone=company.phone,
                address=refreshed_address,
            )

        return VendorUserResponseData(
            id=str(vendor.public_id),
            email=vendor.email,
            full_name=vendor.full_name or "",
            phone=vendor.phone,
            status=vendor.status,
            role=vendor.role,
            is_profile_image_url=vendor.is_profile_image_url,
            company=refreshed_company,
        )

    async def build_vendor_response(self, vendor: User):
        refreshed_company = None
        if vendor.company is not None:
            company = vendor.company
            address = await self.address_service.get_company_address_by_owner_id(company.id, flush=True)
            refreshed_address = None
            if address is not None:
                from app.schemas.vendor_schema import VendorAddressData
                refreshed_address = VendorAddressData(
                    id=str(address.id),
                    address_line1=address.address_line1,
                    address_line2=address.address_line2,
                    postal_code=address.postal_code,
                    country=address.country,
                )
            from app.schemas.vendor_schema import VendorCompanyData, VendorUserResponseData
            refreshed_company = VendorCompanyData(
                id=str(company.id),
                name=company.name,
                email=company.email,
                phone=company.phone,
                address=refreshed_address,
            )
            return VendorUserResponseData(
                id=str(vendor.public_id),
                email=vendor.email,
                full_name=vendor.full_name or "",
                phone=vendor.phone,
                status=vendor.status,
                role=vendor.role,
                is_profile_image_url=vendor.is_profile_image_url,
                company=refreshed_company,
            )
        from app.schemas.vendor_schema import VendorUserResponseData
        return VendorUserResponseData(
            id=str(vendor.public_id),
            email=vendor.email,
            full_name=vendor.full_name or "",
            phone=vendor.phone,
            status=vendor.status,
            role=vendor.role,
            is_profile_image_url=vendor.is_profile_image_url,
            company=None,
        )

    


    async def list(
        self,
        page: int = 1,
        page_size: int = 10,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False
    ) -> list[User]:
        # This method retrieves a paginated list of users, optionally including related data and applying filters.
        return await self.user_repository.list_users(
            page=page,
            page_size=page_size,
            search=search,
            filters=filters,
            with_relations=with_relations,
            flush=flush
        )

    async def update(
            self,
            user: User,
            with_relations: Optional[WithRelations] = None,
            commit: bool = True
    ):
        # This method updates an existing user in the database.
        return await self.user_repository.update(user, with_relations=with_relations, commit=commit)