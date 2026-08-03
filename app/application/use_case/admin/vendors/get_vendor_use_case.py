from typing import Optional

from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.user_model import UserRole
from app.schemas.vendor_schema import VendorUserResponseData
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class GetVendorUseCase(BaseUseCase):

    def __init__(
            self,
            user_service : UserService,
            storage_service: StorageService,
            
            current_user: CurrentUser
    ):
        self.user_service = user_service
        self.storage_service = storage_service
    
        self.current_user = current_user


    async def execute(
            self,
            user_id : str,
            
    ) -> Optional[VendorUserResponseData]: 
        vendor = await self.user_service.get_user_by_public_id(
            public_id=user_id,
            with_relations={
                "company": True,
                
            }
        )

        if not vendor:
            raise AppException(
                status_code=404,
                message="Vendor not found",
                error_code="VENDOR_NOT_FOUND"
            )

        if vendor.role != UserRole.VENDOR:
            raise AppException(
                status_code=400,
                message="User is not a vendor",
                error_code="USER_NOT_VENDOR"
            )
        return await self.user_service.build_vendor_response(
            vendor,
            profile_image_url=self.storage_service.get_display_url(vendor.is_profile_image_url),
        )
        
