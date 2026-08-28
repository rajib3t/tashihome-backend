from fastapi import APIRouter, Depends, File, UploadFile

from app.api.base_controller import BaseController
from app.application.dto.properties.property import AssetsDTO, PropertyAssetsDTO, PropertyDTO, PropertyUpdateDTO, PropertyQueryDTO
from app.application.use_case.vendor.property.create_property_use_case import VendorCreatePropertyUseCase
from app.application.use_case.vendor.property.update_property_use_case import VendorUpdatePropertyUseCase
from app.application.use_case.vendor.property.get_property_use_case import VendorGetPropertyUseCase
from app.application.use_case.vendor.property.get_properties_use_case import GetVendorPropertyUseCase
from app.application.use_case.vendor.property.upload_property_assets_use_case import (
    VendorUploadPropertyAssetsUseCase,
    VendorDeletePropertyAssetUseCase,
)
from app.deps.property import (
    get_vendor_property_list_use_case,
    get_vendor_create_property_use_case,
    get_vendor_update_property_use_case,
    get_vendor_get_property_use_case,
    get_vendor_upload_property_assets_use_case,
    get_vendor_delete_property_asset_use_case,
)
from app.schemas.property_schema import PropertyListResponseSchema, PropertyResponseSchema
from app.utils.exception_decorate import handle_api_exceptions


class PropertyController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/properties",
            tags=["Vendor - Properties"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "/", self._get_properties, {"response_model": PropertyListResponseSchema}),
            ("post", "/", self._create_property, {"response_model": PropertyResponseSchema, "status_code": 201}),
            ("get", "/{property_id}", self._get_property, {"response_model": PropertyResponseSchema}),
            ("put", "/{property_id}", self._update_property, {"response_model": PropertyResponseSchema}),
            ("post", "/{property_id}/media", self._upload_property_media, {"response_model": PropertyResponseSchema, "status_code": 201}),
            ("delete", "/{property_id}/assets/{asset_id}", self._delete_property_asset, {"response_model": PropertyResponseSchema}),
        ]

        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _get_properties(
        self,
        params: PropertyQueryDTO = Depends(),
        use_case: GetVendorPropertyUseCase = Depends(get_vendor_property_list_use_case),
    ):
        properties = await use_case.execute(params)
        return self.build_response(
            message="Properties retrieved successfully.",
            data=properties.items,
            meta=self.pagination_meta(properties),
        )

    @handle_api_exceptions
    async def _create_property(
        self,
        data: PropertyDTO,
        use_case: VendorCreatePropertyUseCase = Depends(get_vendor_create_property_use_case),
    ):
        created_property = await use_case.execute(data)
        return self.build_response(
            message="Property created successfully.",
            data=created_property,
        )

    @handle_api_exceptions
    async def _get_property(
        self,
        property_id: str,
        use_case: VendorGetPropertyUseCase = Depends(get_vendor_get_property_use_case),
    ):
        property_data = await use_case.execute(property_id)
        return self.build_response(
            message="Property retrieved successfully.",
            data=property_data,
        )

    @handle_api_exceptions
    async def _update_property(
        self,
        property_id: str,
        data: PropertyUpdateDTO,
        use_case: VendorUpdatePropertyUseCase = Depends(get_vendor_update_property_use_case),
    ):
        updated_property = await use_case.execute(property_id, data)
        return self.build_response(
            message="Property updated successfully.",
            data=updated_property,
        )

    @handle_api_exceptions
    async def _upload_property_media(
        self,
        property_id: str,
        gallery_images: list[UploadFile] = File(default=[]),
        feature_image: UploadFile | None = File(default=None),
        cover_image: UploadFile | None = File(default=None),
        use_case: VendorUploadPropertyAssetsUseCase = Depends(get_vendor_upload_property_assets_use_case),
    ):
        assets_dto = PropertyAssetsDTO(
            gallery_images=[AssetsDTO(name=image.filename or "gallery", file=image) for image in gallery_images],
            feature_image=AssetsDTO(name=feature_image.filename or "feature", file=feature_image) if feature_image else None,
            cover_image=AssetsDTO(name=cover_image.filename or "cover", file=cover_image) if cover_image else None,
        )
        updated_property = await use_case.execute(property_id, assets_dto)
        return self.build_response(
            message="Property media uploaded successfully.",
            data=updated_property,
        )

    @handle_api_exceptions
    async def _delete_property_asset(
        self,
        property_id: str,
        asset_id: str,
        use_case: VendorDeletePropertyAssetUseCase = Depends(get_vendor_delete_property_asset_use_case),
    ):
        updated_property = await use_case.execute(property_id, asset_id)
        return self.build_response(
            message="Property asset deleted successfully.",
            data=updated_property,
        )


controller = PropertyController()
router = controller.router