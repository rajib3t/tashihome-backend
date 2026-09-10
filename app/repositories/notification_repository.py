from datetime import datetime, timezone
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notification_model import Notification
from app.models.user_model import UserRole
from app.repositories.base_repository import BaseRepository, Page


class NotificationRepository(BaseRepository[Notification]):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create(self, notification: Notification, commit: bool = True) -> Notification:
        self.db.add(notification)
        if commit:
            await self.db.commit()
            await self.db.refresh(notification)
        return notification

    async def bulk_create(self, notifications: Sequence[Notification], commit: bool = True) -> Sequence[Notification]:
        if not notifications:
            return []
        self.db.add_all(notifications)
        if commit:
            await self.db.commit()
            for n in notifications:
                await self.db.refresh(n)
        return notifications

    async def get_by_public_id(self, public_id: str, user_id: Optional[int] = None) -> Optional[Notification]:
        try:
            uuid_obj = UUID(str(public_id))
        except (ValueError, AttributeError):
            return None

        stmt = select(Notification).where(Notification.public_id == uuid_obj)
        if user_id is not None:
            stmt = stmt.where(Notification.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_for_user(
        self,
        user_id: int,
        role: Optional[UserRole] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[Notification]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        count_stmt = select(func.count(Notification.id)).where(Notification.user_id == user_id)

        if role is not None:
            stmt = stmt.where(Notification.role == role)
            count_stmt = count_stmt.where(Notification.role == role)

        if is_read is not None:
            stmt = stmt.where(Notification.is_read == is_read)
            count_stmt = count_stmt.where(Notification.is_read == is_read)

        total_res = await self.db.execute(count_stmt)
        total = total_res.scalar() or 0

        offset = (page - 1) * page_size
        stmt = stmt.order_by(Notification.created_at.desc()).offset(offset).limit(page_size)

        items_res = await self.db.execute(stmt)
        items = list(items_res.scalars().all())

        return Page(items=items, total=total, page=page, page_size=page_size)

    async def count_unread(self, user_id: int, role: Optional[UserRole] = None) -> int:
        count_stmt = select(func.count(Notification.id)).where(
            Notification.user_id == user_id,
            Notification.is_read == False,
        )
        if role is not None:
            count_stmt = count_stmt.where(Notification.role == role)

        res = await self.db.execute(count_stmt)
        return res.scalar() or 0

    async def mark_as_read(self, public_id: str, user_id: int) -> Optional[Notification]:
        notification = await self.get_by_public_id(public_id, user_id=user_id)
        if not notification:
            return None

        if not notification.is_read:
            notification.is_read = True
            notification.read_at = datetime.now(timezone.utc)
            await self.db.commit()
            await self.db.refresh(notification)

        return notification

    async def mark_all_as_read(self, user_id: int, role: Optional[UserRole] = None) -> int:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.is_read == False)
            .values(is_read=True, read_at=now)
        )
        if role is not None:
            stmt = stmt.where(Notification.role == role)

        res = await self.db.execute(stmt)
        await self.db.commit()
        return res.rowcount

    async def delete_for_user(self, public_id: str, user_id: int) -> bool:
        notification = await self.get_by_public_id(public_id, user_id=user_id)
        if not notification:
            return False

        await self.db.delete(notification)
        await self.db.commit()
        return True
