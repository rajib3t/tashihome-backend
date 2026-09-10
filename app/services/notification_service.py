import logging
from typing import Any, Optional, Sequence

from sqlalchemy import inspect as sa_inspect, select

from app.core.socket import emit_notification, emit_to_admins, emit_to_user
from app.models.booking_model import Booking, BookingStatus
from app.models.host_request_model import HostRequest
from app.models.notification_model import Notification, NotificationType
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.notification_repository import NotificationRepository
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(
        self,
        notification_repository: NotificationRepository,
        user_repository: Optional[UserRepository] = None,
    ):
        self.repo = notification_repository
        self.user_repo = user_repository

    async def _get_active_admin_ids(self) -> list[int]:
        """Fetch IDs of all active platform administrators."""
        session = self.repo.db
        stmt = select(User.id).where(
            User.role == UserRole.ADMIN,
            User.status == UserStatus.ACTIVE,
        )
        res = await session.execute(stmt)
        return list(res.scalars().all())

    def _build_payload(self, notif: Notification) -> dict[str, Any]:
        """Build JSON-safe dict for real-time Socket.IO emission."""
        role_str = notif.role.value if hasattr(notif.role, "value") else str(notif.role)
        return {
            "id": str(notif.public_id),
            "role": role_str,
            "type": notif.type,
            "title": notif.title,
            "message": notif.message,
            "data": notif.data,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }

    async def send_notification(
        self,
        user_id: int,
        role: UserRole,
        type: str,
        title: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
    ) -> Notification:
        """Persist a single notification in DB and emit via Socket.IO."""
        notif = Notification(
            user_id=user_id,
            role=role,
            type=type,
            title=title,
            message=message,
            data=data,
        )
        saved = await self.repo.create(notif, commit=True)
        payload = self._build_payload(saved)

        try:
            role_str = role.value if hasattr(role, "value") else str(role)
            await emit_notification(user_id=user_id, role=role_str, payload=payload)
        except Exception as exc:
            logger.warning("Failed to emit real-time socket notification: %s", exc)

        return saved

    async def send_notification_to_admins(
        self,
        type: str,
        title: str,
        message: str,
        data: Optional[dict[str, Any]] = None,
        exclude_user_ids: Optional[Sequence[int]] = None,
    ) -> list[Notification]:
        """Persist notification records for active admins and broadcast to user socket rooms."""
        admin_ids = await self._get_active_admin_ids()
        if exclude_user_ids:
            exclude_set = set(exclude_user_ids)
            admin_ids = [aid for aid in admin_ids if aid not in exclude_set]

        if not admin_ids:
            logger.info("No active admins found to notify for event '%s'", type)
            return []

        notifications = [
            Notification(
                user_id=admin_id,
                role=UserRole.ADMIN,
                type=type,
                title=title,
                message=message,
                data=data,
            )
            for admin_id in admin_ids
        ]
        saved_list = list(await self.repo.bulk_create(notifications, commit=True))

        try:
            if saved_list:
                for notif in saved_list:
                    await emit_to_user(notif.user_id, "notification", self._build_payload(notif))
        except Exception as exc:
            logger.warning("Failed to emit admin socket notification: %s", exc)

        return saved_list

    # -------------------------------------------------------------------------
    # Booking Request & Booking Lifecycle Orchestrators
    # -------------------------------------------------------------------------

    async def notify_booking_request_created(self, booking: Booking) -> None:
        """
        Triggered when a guest submits a new booking request.
        Notifies:
          - Guest (User): Confirmation that request was submitted
          - Vendor (Host): High-priority action alert to review & confirm request
          - Admins: Platform awareness of new booking request
        """
        prop = None
        guest = None
        try:
            insp = sa_inspect(booking)
            prop = booking.property if hasattr(booking, "property") and "property" not in insp.unloaded else getattr(booking, "property", None)
            guest = booking.guest if hasattr(booking, "guest") and "guest" not in insp.unloaded else getattr(booking, "guest", None)
        except Exception:
            prop = getattr(booking, "property", None)
            guest = getattr(booking, "guest", None)


        prop_name = prop.name if prop and hasattr(prop, "name") else "Homestay"
        vendor_id = prop.vendor_id if prop and hasattr(prop, "vendor_id") else None
        guest_name = guest.full_name if guest and hasattr(guest, "full_name") and guest.full_name else "Guest"
        ref = booking.booking_reference

        metadata = {
            "booking_id": int(booking.id),
            "booking_reference": ref,
            "property_id": int(booking.property_id),
            "property_name": prop_name,
            "check_in_date": str(booking.check_in_date),
            "check_out_date": str(booking.check_out_date),
            "total_amount": float(booking.total_amount),
            "status": booking.status.value if hasattr(booking.status, "value") else str(booking.status),
        }

        # 1. Notify Guest (User)
        await self.send_notification(
            user_id=booking.guest_id,
            role=UserRole.USER,
            type=NotificationType.BOOKING_REQUEST_CREATED.value,
            title="Booking Request Submitted",
            message=f"Your booking request #{ref} for {prop_name} has been submitted and is awaiting host confirmation.",
            data=metadata,
        )

        # 2. Notify Vendor (Host)
        if vendor_id:
            await self.send_notification(
                user_id=vendor_id,
                role=UserRole.VENDOR,
                type=NotificationType.BOOKING_REQUEST_CREATED.value,
                title="New Booking Request Received",
                message=f"You received a new booking request #{ref} from {guest_name} for {prop_name} ({booking.check_in_date} to {booking.check_out_date}). Please review and confirm.",
                data=metadata,
            )

        # 3. Notify Admins (excluding vendor if vendor is an admin and already received direct vendor alert)
        exclude_admins = [vendor_id] if vendor_id else None
        await self.send_notification_to_admins(
            type=NotificationType.BOOKING_REQUEST_CREATED.value,
            title="New Booking Request",
            message=f"Booking request #{ref} was created for {prop_name} by {guest_name}.",
            data=metadata,
            exclude_user_ids=exclude_admins,
        )

    async def notify_booking_status_updated(
        self,
        booking: Booking,
        old_status: Any,
        new_status: Any,
        actor_role: str = "system",
    ) -> None:
        """
        Triggered when a booking request or booking status transitions
        (e.g. pending -> confirmed, pending/confirmed -> cancelled, checked_in, etc.)
        """
        prop = None
        try:
            insp = sa_inspect(booking)
            prop = booking.property if hasattr(booking, "property") and "property" not in insp.unloaded else getattr(booking, "property", None)
        except Exception:
            prop = getattr(booking, "property", None)

        prop_name = prop.name if prop and hasattr(prop, "name") else "Homestay"
        vendor_id = prop.vendor_id if prop and hasattr(prop, "vendor_id") else None
        ref = booking.booking_reference

        new_status_str = new_status.value if hasattr(new_status, "value") else str(new_status).lower()
        old_status_str = old_status.value if hasattr(old_status, "value") else str(old_status).lower()

        metadata = {
            "booking_id": int(booking.id),
            "booking_reference": ref,
            "property_id": int(booking.property_id),
            "property_name": prop_name,
            "old_status": old_status_str,
            "new_status": new_status_str,
            "actor_role": actor_role,
        }

        # Booking Confirmed
        if new_status_str == BookingStatus.CONFIRMED.value:
            # Guest
            await self.send_notification(
                user_id=booking.guest_id,
                role=UserRole.USER,
                type=NotificationType.BOOKING_CONFIRMED.value,
                title="Booking Confirmed",
                message=f"Great news! Your booking request #{ref} for {prop_name} has been confirmed.",
                data=metadata,
            )
            # Vendor
            if vendor_id:
                await self.send_notification(
                    user_id=vendor_id,
                    role=UserRole.VENDOR,
                    type=NotificationType.BOOKING_CONFIRMED.value,
                    title="Booking Confirmed",
                    message=f"Booking #{ref} for {prop_name} is now confirmed.",
                    data=metadata,
                )
            # Admins
            await self.send_notification_to_admins(
                type=NotificationType.BOOKING_CONFIRMED.value,
                title="Booking Confirmed",
                message=f"Booking #{ref} for {prop_name} has been confirmed.",
                data=metadata,
            )

        # Booking Cancelled
        elif new_status_str == BookingStatus.CANCELLED.value:
            reason = getattr(booking, "cancellation_reason", None) or "Cancellation requested"
            metadata["reason"] = reason

            # Guest
            await self.send_notification(
                user_id=booking.guest_id,
                role=UserRole.USER,
                type=NotificationType.BOOKING_CANCELLED.value,
                title="Booking Cancelled",
                message=f"Booking #{ref} for {prop_name} has been cancelled ({reason}).",
                data=metadata,
            )
            # Vendor
            if vendor_id:
                await self.send_notification(
                    user_id=vendor_id,
                    role=UserRole.VENDOR,
                    type=NotificationType.BOOKING_CANCELLED.value,
                    title="Booking Cancelled",
                    message=f"Booking #{ref} for {prop_name} was cancelled ({reason}).",
                    data=metadata,
                )
            # Admins
            await self.send_notification_to_admins(
                type=NotificationType.BOOKING_CANCELLED.value,
                title="Booking Cancelled",
                message=f"Booking #{ref} for {prop_name} was cancelled ({reason}).",
                data=metadata,
            )

        # Other status updates (checked_in, checked_out, completed, no_show)
        else:
            status_title = new_status_str.replace("_", " ").title()
            await self.send_notification(
                user_id=booking.guest_id,
                role=UserRole.USER,
                type=NotificationType.BOOKING_STATUS_CHANGED.value,
                title=f"Booking Status: {status_title}",
                message=f"Your booking #{ref} status is now '{status_title}'.",
                data=metadata,
            )
            if vendor_id:
                await self.send_notification(
                    user_id=vendor_id,
                    role=UserRole.VENDOR,
                    type=NotificationType.BOOKING_STATUS_CHANGED.value,
                    title=f"Booking Status: {status_title}",
                    message=f"Booking #{ref} for {prop_name} status updated to '{status_title}'.",
                    data=metadata,
                )

    # -------------------------------------------------------------------------
    # Host Request Lifecycle Orchestrators
    # -------------------------------------------------------------------------

    async def notify_host_request_submitted(self, host_request: HostRequest) -> None:
        """Triggered when someone submits an application to become a host."""
        metadata = {
            "host_request_id": int(host_request.id),
            "public_id": str(host_request.public_id),
            "full_name": host_request.full_name,
            "email": host_request.email,
            "phone": host_request.phone,
            "property_name": host_request.property_name,
            "city": host_request.city,
        }

        # 1. If applicant is a registered user, send confirmation
        if host_request.user_id:
            await self.send_notification(
                user_id=host_request.user_id,
                role=UserRole.USER,
                type=NotificationType.HOST_REQUEST_SUBMITTED.value,
                title="Host Application Submitted",
                message=f"Thank you {host_request.full_name}, your application to host '{host_request.property_name or 'your homestay'}' has been received. Our team will review it shortly.",
                data=metadata,
            )

        # 2. Notify Admins
        await self.send_notification_to_admins(
            type=NotificationType.HOST_REQUEST_SUBMITTED.value,
            title="New Host Request",
            message=f"New host application received from {host_request.full_name} for '{host_request.property_name or 'Homestay'}' in {host_request.city or 'N/A'}.",
            data=metadata,
        )

    async def notify_host_request_status_updated(
        self,
        host_request: HostRequest,
        old_status: str,
        new_status: str,
        notes: Optional[str] = None,
    ) -> None:
        """Triggered when an admin reviews or changes the host request status."""
        status_clean = new_status.replace("_", " ").title()
        metadata = {
            "host_request_id": int(host_request.id),
            "public_id": str(host_request.public_id),
            "old_status": old_status,
            "new_status": new_status,
            "notes": notes,
        }

        # 1. Notify applicant if registered
        if host_request.user_id:
            msg = f"Your host application status has been updated to '{status_clean}'."
            if notes and notes.strip():
                msg += f" Note: {notes.strip()}"
            await self.send_notification(
                user_id=host_request.user_id,
                role=UserRole.USER,
                type=NotificationType.HOST_REQUEST_STATUS_CHANGED.value,
                title=f"Host Request {status_clean}",
                message=msg,
                data=metadata,
            )

        # 2. Notify Admins
        await self.send_notification_to_admins(
            type=NotificationType.HOST_REQUEST_STATUS_CHANGED.value,
            title="Host Request Status Updated",
            message=f"Host application for {host_request.full_name} was marked as '{status_clean}'.",
            data=metadata,
        )

    async def notify_host_request_converted(
        self,
        host_request: HostRequest,
        converted_user: User,
    ) -> None:
        """Triggered when a host request is approved and converted to an active vendor account."""
        metadata = {
            "host_request_id": int(host_request.id),
            "public_id": str(host_request.public_id),
            "converted_user_id": int(converted_user.id),
            "vendor_email": converted_user.email,
        }

        # 1. Notify converted vendor
        await self.send_notification(
            user_id=converted_user.id,
            role=UserRole.VENDOR,
            type=NotificationType.HOST_REQUEST_CONVERTED.value,
            title="Host Account Activated!",
            message="Congratulations! Your host application has been approved and your vendor account is now active. You can now start adding properties and receiving bookings.",
            data=metadata,
        )

        # 2. Notify Admins
        await self.send_notification_to_admins(
            type=NotificationType.HOST_REQUEST_CONVERTED.value,
            title="Host Application Converted",
            message=f"Host application for {host_request.full_name} has been converted into an active vendor account.",
            data=metadata,
        )

    async def notify_host_request_message(
        self,
        host_request: HostRequest,
        sender_role: str,
        sender_name: str,
        message_snippet: str,
    ) -> None:
        """Triggered when a message is added to a host request thread."""
        metadata = {
            "host_request_id": int(host_request.id),
            "public_id": str(host_request.public_id),
            "sender_role": sender_role,
            "sender_name": sender_name,
        }

        # If admin sent message, notify applicant
        if sender_role == "admin" and host_request.user_id:
            await self.send_notification(
                user_id=host_request.user_id,
                role=UserRole.USER,
                type=NotificationType.HOST_REQUEST_MESSAGE.value,
                title="New Message on Host Application",
                message=f"You received a message regarding your host application: '{message_snippet[:120]}...'",
                data=metadata,
            )
        # If applicant sent message, notify admins
        elif sender_role != "admin":
            await self.send_notification_to_admins(
                type=NotificationType.HOST_REQUEST_MESSAGE.value,
                title="New Host Application Message",
                message=f"New message from applicant {sender_name}: '{message_snippet[:120]}...'",
                data=metadata,
            )
