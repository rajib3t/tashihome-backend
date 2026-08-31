import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class HostRequestMessage(Base):
    __tablename__ = "host_request_messages"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    host_request_id = Column(
        BigInteger,
        ForeignKey("host_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    sender_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    sender_name = Column(String(255), nullable=False)
    sender_role = Column(String(50), nullable=False)  # "admin", "applicant", etc.
    message = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    host_request = relationship("HostRequest", back_populates="messages")
    sender = relationship("User", foreign_keys=[sender_id])

