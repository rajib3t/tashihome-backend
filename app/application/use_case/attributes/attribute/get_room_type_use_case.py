from app.application.dto.attributes.room_type import RoomTypeQueryDTO
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.models.room_type_model import RoomType, RoomTypeStatus
from app.repositories.base_repository import Page
from app.services.room_type_service import RoomTypeService


class ListRoomTypesUseCase(BaseUseCase):
    def __init__(
        self,
        room_type_service: RoomTypeService,
        current_user: CurrentUser,
    ):
        self.room_type_service = room_type_service
        self.current_user = current_user

    async def execute(self, request_dto: RoomTypeQueryDTO) -> Page[RoomType]:
        filters = list(request_dto.filters or [])

        if request_dto.name:
            filters.append({"name": "name", "value": request_dto.name})
        if request_dto.status:
            if request_dto.status not in ["active", "inactive"]:
                raise AppException(
                    status_code=422,
                    message="Invalid status filter. Must be 'active' or 'inactive'.",
                    field="status",
                    error_code="STATUS_INVALID",
                )
        if request_dto.status == "active":
            filters.append({"name": "status", "value": RoomTypeStatus.ACTIVE})
        elif request_dto.status == "inactive":
            filters.append({"name": "status", "value": RoomTypeStatus.INACTIVE})

        return await self.room_type_service.list(
            page=request_dto.page,
            page_size=request_dto.size,
            search=request_dto.name,
            filters=filters,
            flush=True,
        )
