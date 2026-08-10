from app.application.dto.properties.property import PropertyQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.property_model import Property, PropertyStatus
from app.repositories.base_repository import Page
from app.services.property_service import PropertyService
from app.services.storage_service import StorageService
from app.services.user_service import UserService


class GetPropertiesUseCase(BaseUseCase):

    def __init__(
            self,
            property_service : PropertyService,
            storage_service : StorageService,
            user_service : UserService,
            current_user : CurrentUser
    ):
        self.property_service = property_service
        self.storage_service = storage_service
        self.user_service = user_service
        self.current_user = current_user


    async def execute(self, params: PropertyQueryDTO)->Page[Property]:
        filters = list(params.filters or [])

        if params.name:
            filters.append({"name": "name", "value": params.name})
        if params.status:
            normalized_status = params.status.strip().lower()
            if normalized_status not in ["active", "inactive","draft","archived"]:
                raise ValueError("Invalid status filter. Must be 'active' or 'inactive' or 'draft' or 'archived'.")
            filters.append({"name": "status", "value": normalized_status})


        if params.status:
            normalized_status = params.status.strip().lower()
            if normalized_status not in ["active", "inactive","draft","archived"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive' or 'draft' or 'archived'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
        else:
            normalized_status = None

        if normalized_status == "active":
            filters.append({"name": "status", "value": PropertyStatus.ACTIVE})
        elif normalized_status == "inactive":
            filters.append({"name": "status", "value": PropertyStatus.INACTIVE})
        elif normalized_status == "draft":
            filters.append({"name": "status", "value": PropertyStatus.DRAFT})
        elif normalized_status == "archived":
            filters.append({"name": "status", "value": PropertyStatus.ARCHIVED})

        return await self.property_service.list(
            page=params.page,
            page_size=params.size,
            search=params.name,
            filters=filters,
            with_relations={"city": True, "location": True, "vendor": True},
            flush=True
        )