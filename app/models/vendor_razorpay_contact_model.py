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
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class VendorRazorpayContact(Base):
    __tablename__ = "vendor_razorpay_contacts"
    __table_args__ = (
        UniqueConstraint("vendor_id", name="uq_vendor_razorpay_contacts_vendor_id"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    vendor_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    razorpay_contact_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    type = Column(String(50), default="vendor", nullable=False)
    reference_id = Column(String(255), nullable=True)
    active = Column(Boolean, default=True, nullable=False)
    raw_response = Column(Text, nullable=True)  # JSON string of full Razorpay response

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("User", foreign_keys=[vendor_id])
    fund_accounts = relationship(
        "VendorRazorpayFundAccount",
        back_populates="contact",
        cascade="all, delete-orphan",
    )
