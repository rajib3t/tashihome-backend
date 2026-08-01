from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.vendors.vendor import CreateVendorDTO
from app.application.use_case.admin.vendors.create_vendor_use_case import CreateVendorUseCase
from app.deps.venvor import get_create_vendor_use_case
from app.schemas.user_schema import UserResponseSchema


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
            # ("get", "/", self._get_vendors, {"response_model": VendorListResponseSchema}),
            ("post", "/", self._create_vendor, {"response_model": UserResponseSchema, "status_code": 201}),
            # Add more routes as needed
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)


    async def _get_vendors(self):
        # Implement the logic to get vendors
        pass

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
