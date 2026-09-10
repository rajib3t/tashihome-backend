from typing import Optional

from fastapi import APIRouter, Depends, Query

from app.api.base_controller import BaseController
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser, get_current_user
from app.deps.notification import get_notification_repository
from app.models.user_model import UserRole
from app.repositories.notification_repository import NotificationRepository
from app.schemas.notification_schema import (
    NotificationListResponse,
    NotificationMarkAllReadResponse,
    NotificationSingleResponse,
    NotificationUnreadCountResponse,
)
from app.utils.exception_decorate import handle_api_exceptions


class NotificationController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/notifications",
            tags=["Notifications"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("get", "", self._list_notifications, {"response_model": NotificationListResponse}),
            ("get", "/", self._list_notifications, {"response_model": NotificationListResponse, "include_in_schema": False}),
            ("get", "/unread-count", self._get_unread_count, {"response_model": NotificationUnreadCountResponse}),
            ("patch", "/read-all", self._mark_all_read, {"response_model": NotificationMarkAllReadResponse}),
            ("patch", "/{public_id}/read", self._mark_read, {"response_model": NotificationSingleResponse}),
            ("delete", "/{public_id}", self._delete_notification, {}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _list_notifications(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(20, ge=1, le=100, description="Items per page"),
        is_read: Optional[bool] = Query(None, description="Filter by read status"),
        role: Optional[UserRole] = Query(None, description="Filter by role context"),
        current_user: CurrentUser = Depends(get_current_user),
        repo: NotificationRepository = Depends(get_notification_repository),
    ):
        page_result = await repo.list_for_user(
            user_id=current_user.id,
            role=role,
            is_read=is_read,
            page=page,
            page_size=page_size,
        )
        unread_count = await repo.count_unread(user_id=current_user.id, role=role)

        meta = {
            "total": page_result.total,
            "page": page_result.page,
            "size": page_result.page_size,
            "total_pages": page_result.pages,
            "unread_count": unread_count,
        }

        return self.build_response(
            message="Notifications retrieved successfully",
            data=page_result.items,
            meta=meta,
        )

    @handle_api_exceptions
    async def _get_unread_count(
        self,
        role: Optional[UserRole] = Query(None, description="Filter by role context"),
        current_user: CurrentUser = Depends(get_current_user),
        repo: NotificationRepository = Depends(get_notification_repository),
    ):
        count = await repo.count_unread(user_id=current_user.id, role=role)
        return self.build_response(
            message="Unread notification count retrieved",
            data={"unread_count": count},
        )

    @handle_api_exceptions
    async def _mark_read(
        self,
        public_id: str,
        current_user: CurrentUser = Depends(get_current_user),
        repo: NotificationRepository = Depends(get_notification_repository),
    ):
        notification = await repo.mark_as_read(public_id=public_id, user_id=current_user.id)
        if not notification:
            raise AppException(
                status_code=404,
                message="Notification not found",
                error_code="NOTIFICATION_NOT_FOUND",
            )
        return self.build_response(
            message="Notification marked as read",
            data=notification,
        )

    @handle_api_exceptions
    async def _mark_all_read(
        self,
        role: Optional[UserRole] = Query(None, description="Filter by role context"),
        current_user: CurrentUser = Depends(get_current_user),
        repo: NotificationRepository = Depends(get_notification_repository),
    ):
        updated_count = await repo.mark_all_as_read(user_id=current_user.id, role=role)
        return self.build_response(
            message=f"Marked {updated_count} notification(s) as read",
            data={"updated_count": updated_count},
        )

    @handle_api_exceptions
    async def _delete_notification(
        self,
        public_id: str,
        current_user: CurrentUser = Depends(get_current_user),
        repo: NotificationRepository = Depends(get_notification_repository),
    ):
        deleted = await repo.delete_for_user(public_id=public_id, user_id=current_user.id)
        if not deleted:
            raise AppException(
                status_code=404,
                message="Notification not found",
                error_code="NOTIFICATION_NOT_FOUND",
            )
        return self.build_response(
            message="Notification deleted successfully",
            data={"id": public_id},
        )


controller = NotificationController()
router = controller.router
