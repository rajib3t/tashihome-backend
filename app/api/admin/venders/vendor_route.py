from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.vendors.vendor import CreateVendorDTO, VendorQueryDTO
from app.application.use_case.admin.vendors.create_vendor_use_case import CreateVendorUseCase
from app.application.use_case.admin.vendors.list_vendor_use_case import ListVendorUseCase
from app.deps.vendor import get_create_vendor_use_case, get_list_vendor_use_case
from app.schemas.user_schema import UserListResponseSchema, UserResponseSchema


class VendorController(BaseController):
    def __init__(self):

        self.router = APIRouter(
            prefix="/vendors",
            tags=["Vendors"],
        )
        self._register_routes()


    def _register_routes(self):
        routes = [
            # Define your routes here, for example:
            ("get", "/", self._get_vendors, {"response_model": UserListResponseSchema}),
            ("post", "/", self._create_vendor, {"response_model": UserResponseSchema, "status_code": 201}),
            # Add more routes as needed
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


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

    async def _create_vendor(
        self,
        data: CreateVendorDTO,
        use_case : CreateVendorUseCase = Depends(get_create_vendor_use_case)
    ):
        
        vendor = await use_case.execute(data)
        return self.build_response(
            message="Vendor created successfully.",
            data=vendor,
        )

controller = VendorController()
router = controller.router
