import enum
import uuid

from sqlalchemy import (
    JSON,
    UUID,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.user_model import UserRole


class NotificationType(str, enum.Enum):
    # Booking Request & Booking Lifecycle
    BOOKING_REQUEST_CREATED = "booking.request_created"
    BOOKING_CONFIRMED = "booking.confirmed"
    BOOKING_CANCELLED = "booking.cancelled"
    BOOKING_STATUS_CHANGED = "booking.status_changed"

    # Host Request Lifecycle
    HOST_REQUEST_SUBMITTED = "host_request.submitted"
    HOST_REQUEST_STATUS_CHANGED = "host_request.status_changed"
    HOST_REQUEST_CONVERTED = "host_request.converted"
    HOST_REQUEST_MESSAGE = "host_request.message"

    # Generic / System
    SYSTEM = "system"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    role = Column(
        Enum(UserRole),
        nullable=False,
        index=True,
        doc="The role context in which the user received this notification (admin, vendor, user, etc.)",
    )

    type = Column(
        String(60),
        nullable=False,
        index=True,
        doc="Event type identifier (e.g. booking.request_created, host_request.submitted)",
    )

    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)

    data = Column(
        JSON,
        nullable=True,
        doc="Arbitrary structured metadata (e.g. booking_reference, property_id, host_request_id)",
    )

    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationship
    user = relationship("User", back_populates="notifications")
