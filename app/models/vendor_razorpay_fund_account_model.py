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


class VendorRazorpayFundAccount(Base):
    __tablename__ = "vendor_razorpay_fund_accounts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    contact_id = Column(
        BigInteger,
        ForeignKey("vendor_razorpay_contacts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    bank_account_id = Column(
        BigInteger,
        ForeignKey("vendor_bank_accounts.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
        index=True,
    )

    razorpay_fund_account_id = Column(String(255), unique=True, nullable=False, index=True)
    account_type = Column(String(50), nullable=False)  # "bank_account" or "vpa"
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
    contact = relationship("VendorRazorpayContact", back_populates="fund_accounts")
    bank_account = relationship("VendorBankAccount", back_populates="razorpay_fund_account")
