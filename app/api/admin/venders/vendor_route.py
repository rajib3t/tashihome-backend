from fastapi import APIRouter, Depends, File, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.vendors.vendor import (
    AdminConvertUserToHostDTO,
    AdminOnboardHostDTO,
    VendorDTO,
    VendorQueryDTO,
    VendorResetLinkDTO,
    VendorUpdateDTO,
)
from app.application.use_case.admin.vendors.convert_user_use_case import ConvertUserToVendorUseCase
from app.application.use_case.admin.vendors.create_vendor_use_case import CreateVendorUseCase
from app.application.use_case.admin.vendors.get_vendor_use_case import GetVendorUseCase
from app.application.use_case.admin.vendors.list_vendor_use_case import ListVendorUseCase
from app.application.use_case.admin.vendors.onboard_host_use_case import AdminOnboardHostUseCase
from app.application.use_case.admin.vendors.send_password_reset_link_use_case import SendPasswordResetLinkUseCase
from app.application.use_case.admin.vendors.update_vendor_use_case import UpdateStatusVendorUseCase, UpdateVendorUseCase, UploadVendorProfileImageUseCase
from app.deps.vendor import (
    get_admin_onboard_host_use_case,
    get_convert_user_use_case,
    get_create_vendor_use_case,
    get_list_vendor_use_case,
    get_send_password_reset_link_use_case,
    get_update_vendor_status_use_case,
    get_update_vendor_use_case,
    get_upload_vendor_profile_image_use_case,
    get_vendor_use_case,
)
from app.schemas.user_schema import UserListResponseSchema, UserResponseSchema
from app.schemas.vendor_schema import VendorResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class VendorController(BaseController):
    def __init__(self):

        self.router = APIRouter(
            prefix="/vendors",
            tags=["Admin - Vendors"],
        )
        self._register_routes()


    def _register_routes(self):
        routes = [
            ("get", "/", self._get_vendors, {"response_model": UserListResponseSchema}),
            ("post", "/", self._create_vendor, {"response_model": UserResponseSchema, "status_code": 201}),
            ("post", "/onboard", self._onboard_host, {"response_model": VendorResponseSchema, "status_code": 201}),
            ("get", "/{vendor_id}", self._get_vendor, {"response_model": VendorResponseSchema}),
            ("put", "/{vendor_id}", self._update_vendor, {"response_model": VendorResponseSchema}),
            ("patch", "/{vendor_id}/profile-image", self._update_vendor_profile_image, {"response_model": VendorResponseSchema}),
            ("patch", "/change/{vendor_id}/{status}", self._update_vendor_status, {"response_model": VendorResponseSchema}),
            ("post", "/{vendor_id}/password-reset", self._send_password_reset_link, {"response_model": None, "status_code": 200}),
            ("post", "/{vendor_id}/convert", self._convert_user_to_host, {"response_model": VendorResponseSchema}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_vendors(
        self,
        params: VendorQueryDTO = Depends(),
        use_case: ListVendorUseCase = Depends(get_list_vendor_use_case)
        ):

        vendors_page = await use_case.execute(params)
        return self.build_response(
            message="Vendors retrieved successfully.",
            data=vendors_page.items,
            meta=self.pagination_meta(vendors_page),
        )
    @handle_api_exceptions
    async def _create_vendor(
        self,
        data: VendorDTO,
        use_case : CreateVendorUseCase = Depends(get_create_vendor_use_case)
    ):
        
        vendor = await use_case.execute(data)
        return self.build_response(
            message="Vendor created successfully.",
            data=vendor,
        )
    @handle_api_exceptions
    async def _get_vendor(
        self,
        vendor_id: str,
        use_case: GetVendorUseCase = Depends(get_vendor_use_case)
    ):
        vendor = await use_case.execute(vendor_id)
       
        return self.build_response(
            message="Vendor retrieved successfully.",
            data=vendor,
        )
    @handle_api_exceptions
    async def _update_vendor(
        self,
        vendor_id: str,
        data: VendorUpdateDTO,
        use_case: UpdateVendorUseCase = Depends(get_update_vendor_use_case),
    ):
        vendor = await use_case.execute(vendor_id, data)
        return self.build_response(
            message="Vendor updated successfully.",
            data=vendor,
        )
    @handle_api_exceptions 
    async def _update_vendor_profile_image(
        self,
        vendor_id: str,
        profile_image: UploadFile = File(...),
        use_case: UploadVendorProfileImageUseCase = Depends(get_upload_vendor_profile_image_use_case),
    ):
        vendor = await use_case.execute(vendor_id, profile_image)
        return self.build_response(
            message="Vendor profile image updated successfully.",
            data=vendor,
        )
    @handle_api_exceptions
    async def _update_vendor_status(
        self,
        vendor_id: str,
        status: str,
        use_case: UpdateStatusVendorUseCase = Depends(get_update_vendor_status_use_case)
    ):
        vendor = await use_case.execute(vendor_id, status)
        return self.build_response(
            message="Vendor status updated successfully.",
            data=vendor,
        )
    @handle_api_exceptions
    async def _onboard_host(
        self,
        data: AdminOnboardHostDTO,
        use_case: AdminOnboardHostUseCase = Depends(get_admin_onboard_host_use_case),
    ):
        host = await use_case.execute(data)
        return self.build_response(
            message="Host onboarded successfully.",
            data=host,
        )

    @handle_api_exceptions
    async def _send_password_reset_link(
        self,
        vendor_id: str,
        data: VendorResetLinkDTO,
        use_case: SendPasswordResetLinkUseCase = Depends(get_send_password_reset_link_use_case)
    ):
        await use_case.execute(vendor_id, data)
        return self.build_response(
            message="Password reset link sent successfully.",
            data=None,
        )

    @handle_api_exceptions
    async def _convert_user_to_host(
        self,
        vendor_id: str,
        data: AdminConvertUserToHostDTO,
        use_case: ConvertUserToVendorUseCase = Depends(get_convert_user_use_case),
    ):
        host = await use_case.execute(vendor_id, data)
        return self.build_response(
            message="User converted to host successfully.",
            data=host,
        )


controller = VendorController()
router = controller.router

