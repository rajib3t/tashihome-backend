import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class ReviewStatus(str, enum.Enum):
    PUBLISHED = "published"
    HIDDEN = "hidden"
    FLAGGED = "flagged"


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="chk_reviews_rating"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    booking_id = Column(
        BigInteger,
        ForeignKey("bookings.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
    )
    guest_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    property_id = Column(
        BigInteger,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating = Column(SmallInteger, nullable=False)
    comment = Column(Text, nullable=True)
    host_reply = Column(Text, nullable=True)
    host_replied_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(ReviewStatus),
        default=ReviewStatus.PUBLISHED,
        nullable=False,
        index=True,
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    booking = relationship("Booking", back_populates="review")
    guest = relationship("User", foreign_keys=[guest_id])
    property = relationship("Property", back_populates="reviews")

