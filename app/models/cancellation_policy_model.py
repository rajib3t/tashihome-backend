import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.core.database import Base


class CancellationPolicyStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class CancellationPolicy(Base):
    __tablename__ = "cancellation_policies"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    refund_tiers = Column(JSONB, nullable=False)
    status = Column(
        Enum(CancellationPolicyStatus),
        default=CancellationPolicyStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    properties = relationship("Property", back_populates="cancellation_policy")
    bookings = relationship("Booking", back_populates="cancellation_policy")
