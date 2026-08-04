import re
from typing import Optional

from app.application.dto.properties.property import PropertyDTO, PropertyQueryDTO, PropertyUpdateDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_model import Property, PropertyStatus
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService


class ListPropertiesUseCase(BaseUseCase):
    def __init__(self, property_service: PropertyService, current_user: CurrentUser):
        self.property_service = property_service
        self.current_user = current_user

    @staticmethod
    def _normalize_status(status_value: Optional[str]) -> Optional[PropertyStatus]:
        if status_value is None:
            return None
        status_text = status_value.strip().lower()
        valid_statuses = {item.value for item in PropertyStatus}
        if status_text not in valid_statuses:
            raise AppException(
                status_code=422,
                message="Status must be one of: draft, active, inactive, archived.",
                field="status",
                error_code="STATUS_INVALID",
            )
        return PropertyStatus(status_text)

    async def execute(self, params: PropertyQueryDTO) -> Page[Property]:
        filters = list(params.filters or [])

        if params.name:
            filters.append({"name": "name", "value": params.name})
        if params.slug:
            filters.append({"name": "slug", "value": params.slug})
        if params.vendor_id is not None:
            filters.append({"name": "vendor_id", "value": str(params.vendor_id)})
        if params.location_id is not None:
            filters.append({"name": "location_id", "value": str(params.location_id)})
        if params.city_id is not None:
            filters.append({"name": "city_id", "value": str(params.city_id)})
        if params.room_type_id is not None:
            filters.append({"name": "room_type_id", "value": str(params.room_type_id)})
        if params.status:
            normalized_status = self._normalize_status(params.status)
            filters.append({"name": "status", "value": normalized_status.value})

        return await self.property_service.list(
            page=params.page,
            page_size=params.size,
            search=params.name or params.slug,
            filters=filters,
            flush=True,
        )


class CreatePropertyUseCase(BaseUseCase):
    def __init__(self, property_service: PropertyService, current_user: CurrentUser):
        self.property_service = property_service
        self.current_user = current_user

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = (value or "").strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
        slug = slug.strip("-")
        return slug or "property"

    @staticmethod
    def _normalize_status(status_value: Optional[str]) -> PropertyStatus:
        status_text = (status_value or "draft").strip().lower()
        valid_statuses = {item.value for item in PropertyStatus}
        if status_text not in valid_statuses:
            raise AppException(
                status_code=422,
                message="Status must be one of: draft, active, inactive, archived.",
                field="status",
                error_code="STATUS_INVALID",
            )
        return PropertyStatus(status_text)

    async def execute(self, data: PropertyDTO) -> Property:
        duplicate_name = await self.property_service.get_by_vendor_and_name(data.vendor_id, data.name, flush=True)
        if duplicate_name:
            raise AppException(
                status_code=409,
                message="A property with this name already exists for this vendor.",
                field="name",
                error_code="PROPERTY_NAME_EXIST",
            )

        slug = self._slugify(data.slug or data.name)
        duplicate_slug = await self.property_service.get_by_vendor_and_slug(data.vendor_id, slug, flush=True)
        if duplicate_slug:
            raise AppException(
                status_code=409,
                message="A property with this slug already exists for this vendor.",
                field="slug",
                error_code="PROPERTY_SLUG_EXIST",
            )

        property_model = Property(
            vendor_id=data.vendor_id,
            location_id=data.location_id,
            city_id=data.city_id,
            room_type_id=data.room_type_id,
            name=data.name.strip(),
            slug=slug,
            description=data.description,
            main_image_url=data.main_image_url,
            cover_image_url=data.cover_image_url,
            max_guests=data.max_guests,
            price_per_night=data.price_per_night,
            currency=data.currency.upper(),
            is_featured=data.is_featured,
            status=self._normalize_status(data.status),
            created_by=self.current_user.id,
            updated_by=self.current_user.id,
        )

        return await self.property_service.create(property_model)


class UpdatePropertyUseCase(BaseUseCase):
    def __init__(self, property_service: PropertyService, current_user: CurrentUser):
        self.property_service = property_service
        self.current_user = current_user

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = (value or "").strip().lower()
        slug = re.sub(r"[^a-z0-9]+", "-", normalized)
        slug = slug.strip("-")
        return slug or "property"

    @staticmethod
    def _normalize_status(status_value: Optional[str]) -> PropertyStatus:
        status_text = (status_value or "draft").strip().lower()
        valid_statuses = {item.value for item in PropertyStatus}
        if status_text not in valid_statuses:
            raise AppException(
                status_code=422,
                message="Status must be one of: draft, active, inactive, archived.",
                field="status",
                error_code="STATUS_INVALID",
            )
        return PropertyStatus(status_text)

    async def execute(self, property_id: str, data: PropertyUpdateDTO) -> Property:
        existing_property = await self.property_service.get_by_public_id(property_id, flush=False)
        if not existing_property:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        if data.name:
            duplicate_name = await self.property_service.get_by_vendor_and_name(existing_property.vendor_id, data.name, flush=True)
            if duplicate_name and duplicate_name.id != existing_property.id:
                raise AppException(
                    status_code=409,
                    message="A property with this name already exists for this vendor.",
                    field="name",
                    error_code="PROPERTY_NAME_EXIST",
                )

        if data.slug:
            new_slug = self._slugify(data.slug)
            duplicate_slug = await self.property_service.get_by_vendor_and_slug(existing_property.vendor_id, new_slug, flush=True)
            if duplicate_slug and duplicate_slug.id != existing_property.id:
                raise AppException(
                    status_code=409,
                    message="A property with this slug already exists for this vendor.",
                    field="slug",
                    error_code="PROPERTY_SLUG_EXIST",
                )

        if data.name is not None:
            existing_property.name = data.name.strip()
        if data.slug is not None:
            existing_property.slug = self._slugify(data.slug)
        if data.description is not None:
            existing_property.description = data.description
        if data.location_id is not None:
            existing_property.location_id = data.location_id
        if data.city_id is not None:
            existing_property.city_id = data.city_id
        if data.room_type_id is not None:
            existing_property.room_type_id = data.room_type_id
        if data.main_image_url is not None:
            existing_property.main_image_url = data.main_image_url
        if data.cover_image_url is not None:
            existing_property.cover_image_url = data.cover_image_url
        if data.max_guests is not None:
            existing_property.max_guests = data.max_guests
        if data.price_per_night is not None:
            existing_property.price_per_night = data.price_per_night
        if data.currency is not None:
            existing_property.currency = data.currency.upper()
        if data.is_featured is not None:
            existing_property.is_featured = data.is_featured
        if data.status is not None:
            existing_property.status = self._normalize_status(data.status)

        existing_property.updated_by = self.current_user.id
        return await self.property_service.update(existing_property)


class UpdateStatusPropertyUseCase(BaseUseCase):
    def __init__(self, property_service: PropertyService, current_user: CurrentUser):
        self.property_service = property_service
        self.current_user = current_user

    @staticmethod
    def _normalize_status(status_value: str) -> PropertyStatus:
        status_text = (status_value or "").strip().lower()
        valid_statuses = {item.value for item in PropertyStatus}
        if status_text not in valid_statuses:
            raise AppException(
                status_code=422,
                message="Status must be one of: draft, active, inactive, archived.",
                field="status",
                error_code="STATUS_INVALID",
            )
        return PropertyStatus(status_text)

    async def execute(self, property_id: str, status: str) -> Property:
        existing_property = await self.property_service.get_by_public_id(property_id, flush=False)
        if not existing_property:
            raise AppException(
                status_code=404,
                message="Property not found.",
                field="property_id",
                error_code="PROPERTY_NOT_FOUND",
            )

        existing_property.status = self._normalize_status(status)
        existing_property.updated_by = self.current_user.id
        return await self.property_service.update(existing_property)
