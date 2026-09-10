import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone
import uuid

from app.models.notification_model import Notification, NotificationType
from app.models.user_model import User, UserRole, UserStatus
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.host_request_model import HostRequest, HostRequestStatus
from app.repositories.notification_repository import NotificationRepository
from app.services.notification_service import NotificationService
from app.deps.auth import CurrentUser
from app.api.notification_route import NotificationController


def test_notification_repository_crud():
    async def run():
        mock_session = AsyncMock()
        repo = NotificationRepository(mock_session)

        notif = Notification(
            public_id=uuid.uuid4(),
            user_id=1,
            role=UserRole.USER,
            type=NotificationType.BOOKING_REQUEST_CREATED.value,
            title="Booking Request Submitted",
            message="Your booking request has been submitted",
            data={"booking_reference": "BK-1234"},
        )


        # 1. Create
        saved = await repo.create(notif, commit=True)
        assert saved.user_id == 1
        mock_session.add.assert_called_once_with(notif)
        mock_session.commit.assert_called_once()

        # 2. Mark as read
        mock_exec_result = MagicMock()
        mock_exec_result.scalar_one_or_none.return_value = notif
        mock_session.execute.return_value = mock_exec_result

        updated = await repo.mark_as_read(str(notif.public_id), user_id=1)
        assert updated.is_read is True
        assert updated.read_at is not None

        # 3. Delete
        deleted = await repo.delete_for_user(str(notif.public_id), user_id=1)
        assert deleted is True
        mock_session.delete.assert_called_once_with(notif)

    asyncio.run(run())


def test_notification_service_send_notification():
    async def run():
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = lambda n, commit=True: n
        service = NotificationService(notification_repository=mock_repo)

        with patch("app.services.notification_service.emit_notification", new=AsyncMock()) as mock_emit:
            result = await service.send_notification(
                user_id=10,
                role=UserRole.VENDOR,
                type=NotificationType.BOOKING_REQUEST_CREATED.value,
                title="New Booking Request Received",
                message="You received a new booking request",
                data={"booking_id": 42},
            )

            assert result.user_id == 10
            assert result.role == UserRole.VENDOR
            assert result.title == "New Booking Request Received"
            mock_repo.create.assert_called_once()
            mock_emit.assert_called_once()

    asyncio.run(run())


def test_notification_service_booking_request_created():
    async def run():
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = lambda n, commit=True: n
        mock_repo.bulk_create.side_effect = lambda ns, commit=True: ns
        mock_repo.db = AsyncMock()

        # Mock active admins query
        mock_res = MagicMock()
        mock_res.scalars().all.return_value = [999]
        mock_repo.db.execute.return_value = mock_res

        service = NotificationService(notification_repository=mock_repo)

        mock_booking = MagicMock(spec=Booking)
        mock_booking.id = 1
        mock_booking.public_id = uuid.uuid4()
        mock_booking.booking_reference = "BK-2026-TEST"
        mock_booking.guest_id = 100
        mock_booking.property_id = 200
        mock_booking.check_in_date = "2026-10-01"
        mock_booking.check_out_date = "2026-10-05"
        mock_booking.total_amount = 5000.0
        mock_booking.status = BookingStatus.PENDING

        mock_prop = MagicMock()
        mock_prop.name = "Cozy Cottage"
        mock_prop.vendor_id = 50
        mock_booking.property = mock_prop

        mock_guest = MagicMock()
        mock_guest.full_name = "Alice Guest"
        mock_booking.guest = mock_guest

        with patch("app.services.notification_service.emit_notification", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_admins", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_user", new=AsyncMock()):

            await service.notify_booking_request_created(mock_booking)

            # Should send 1 to Guest (repo.create), 1 to Vendor (repo.create), 1 to Admins (repo.bulk_create)
            assert mock_repo.create.call_count == 2
            assert mock_repo.bulk_create.call_count == 1

    asyncio.run(run())


def test_notification_service_booking_status_updated():
    async def run():
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = lambda n, commit=True: n
        mock_repo.bulk_create.side_effect = lambda ns, commit=True: ns
        mock_repo.db = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalars().all.return_value = [999]
        mock_repo.db.execute.return_value = mock_res

        service = NotificationService(notification_repository=mock_repo)

        mock_booking = MagicMock(spec=Booking)
        mock_booking.id = 1
        mock_booking.booking_reference = "BK-2026-CONFIRM"
        mock_booking.guest_id = 100
        mock_booking.property_id = 200
        mock_booking.status = BookingStatus.CONFIRMED

        mock_prop = MagicMock()
        mock_prop.name = "Cozy Cottage"
        mock_prop.vendor_id = 50
        mock_booking.property = mock_prop

        with patch("app.services.notification_service.emit_notification", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_admins", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_user", new=AsyncMock()):

            # Confirm booking
            await service.notify_booking_status_updated(
                mock_booking,
                old_status=BookingStatus.PENDING,
                new_status=BookingStatus.CONFIRMED,
                actor_role="vendor",
            )
            assert mock_repo.create.call_count == 2
            assert mock_repo.bulk_create.call_count == 1

    asyncio.run(run())


def test_notification_service_host_request_submitted():
    async def run():
        mock_repo = AsyncMock()
        mock_repo.create.side_effect = lambda n, commit=True: n
        mock_repo.bulk_create.side_effect = lambda ns, commit=True: ns
        mock_repo.db = AsyncMock()
        mock_res = MagicMock()
        mock_res.scalars().all.return_value = [999]
        mock_repo.db.execute.return_value = mock_res

        service = NotificationService(notification_repository=mock_repo)

        mock_host_req = MagicMock(spec=HostRequest)
        mock_host_req.id = 10
        mock_host_req.public_id = uuid.uuid4()
        mock_host_req.user_id = 100
        mock_host_req.full_name = "Karma Dorji"
        mock_host_req.email = "karma@example.com"
        mock_host_req.phone = "+97517123456"
        mock_host_req.property_name = "Tashi Villa"
        mock_host_req.city = "Paro"

        with patch("app.services.notification_service.emit_notification", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_admins", new=AsyncMock()), \
             patch("app.services.notification_service.emit_to_user", new=AsyncMock()):

            await service.notify_host_request_submitted(mock_host_req)
            assert mock_repo.create.call_count == 1  # 1 to applicant
            assert mock_repo.bulk_create.call_count == 1  # 1 to admins

    asyncio.run(run())


def test_notification_controller_routes():
    async def run():
        controller = NotificationController()
        mock_repo = AsyncMock()

        # Test _list_notifications
        mock_page = MagicMock()
        mock_page.items = []
        mock_page.total = 0
        mock_page.page = 1
        mock_page.page_size = 20
        mock_page.pages = 0
        mock_repo.list_for_user.return_value = mock_page
        mock_repo.count_unread.return_value = 0

        current_user = CurrentUser(id=1, role="user")
        res = await controller._list_notifications(
            page=1,
            page_size=20,
            is_read=None,
            role=None,
            current_user=current_user,
            repo=mock_repo,
        )
        assert res["status"] == "success"
        assert res["meta"]["unread_count"] == 0

        # Test _get_unread_count
        unread_res = await controller._get_unread_count(
            role=None,
            current_user=current_user,
            repo=mock_repo,
        )
        assert unread_res["data"]["unread_count"] == 0

    asyncio.run(run())
