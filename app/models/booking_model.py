import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class BookingStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    PAID = "paid"
    PARTIALLY_PAID = "partially_paid"
    REFUNDED = "refunded"
    FAILED = "failed"


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        CheckConstraint("check_out_date > check_in_date", name="chk_booking_dates"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    booking_reference = Column(String(20), unique=True, nullable=False, index=True)
    guest_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    property_id = Column(
        BigInteger,
        ForeignKey("properties.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    room_type_id = Column(
        BigInteger,
        ForeignKey("room_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    cancellation_policy_id = Column(
        BigInteger,
        ForeignKey("cancellation_policies.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    check_in_date = Column(Date, nullable=False, index=True)
    check_out_date = Column(Date, nullable=False, index=True)
    num_guests = Column(Integer, nullable=False, default=1)
    num_rooms = Column(Integer, nullable=False, default=1)

    price_per_night = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), default=0)
    tax_amount = Column(Numeric(12, 2), default=0)
    total_amount = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(10), default="INR")

    status = Column(
        Enum(BookingStatus),
        default=BookingStatus.PENDING,
        nullable=False,
        index=True,
    )
    payment_status = Column(
        Enum(PaymentStatus),
        default=PaymentStatus.PENDING,
        nullable=False,
        index=True,
    )

    special_requests = Column(Text, nullable=True)
    cancellation_reason = Column(String(255), nullable=True)
    cancelled_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    guest = relationship("User", foreign_keys=[guest_id], back_populates="bookings")
    property = relationship("Property", back_populates="bookings")
    room_type = relationship("RoomType")
    cancellation_policy = relationship("CancellationPolicy", back_populates="bookings")

    payments = relationship(
        "Payment",
        back_populates="booking",
        cascade="all, delete-orphan",
    )
    refund_requests = relationship("RefundRequest", back_populates="booking")
    review = relationship("Review", back_populates="booking", uselist=False)
