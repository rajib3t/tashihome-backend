import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TestimonialStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    HIDDEN = "hidden"


class Testimonial(Base):
    __tablename__ = "testimonials"
    __table_args__ = (
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="chk_testimonials_rating",
        ),
    )

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
    user_role = Column(String(50), nullable=False, index=True, default="user")
    name = Column(String(255), nullable=False)
    designation = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    rating = Column(SmallInteger, nullable=True)
    content = Column(Text, nullable=False)
    status = Column(
        Enum(TestimonialStatus),
        default=TestimonialStatus.PENDING,
        nullable=False,
        index=True,
    )
    is_featured = Column(Boolean, default=False, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id])

