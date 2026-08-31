import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class HostRequestStatus(str, enum.Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    CONVERTED = "converted"


class HostRequest(Base):
    __tablename__ = "host_requests"

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
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    full_name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, index=True)
    phone = Column(String(20), nullable=False, index=True)

    company_name = Column(String(255), nullable=True)
    property_name = Column(String(255), nullable=True)
    property_type = Column(String(50), nullable=True)
    city = Column(String(100), nullable=True)
    address = Column(String(255), nullable=True)
    expected_rooms = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    status = Column(
        Enum(HostRequestStatus),
        default=HostRequestStatus.PENDING,
        nullable=False,
        index=True,
    )

    reviewed_by = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    converted_user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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
    messages = relationship(
        "HostRequestMessage",
        back_populates="host_request",
        cascade="all, delete-orphan",
        order_by="HostRequestMessage.created_at.asc()",
    )
    applicant_user = relationship("User", foreign_keys=[user_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    converted_user = relationship("User", foreign_keys=[converted_user_id])

