import enum
import uuid

from sqlalchemy import (
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


class BankAccountType(str, enum.Enum):
    BANK_ACCOUNT = "bank_account"
    VPA = "vpa"


class VendorBankAccount(Base):
    __tablename__ = "vendor_bank_accounts"

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

    account_type = Column(
        Enum(BankAccountType),
        default=BankAccountType.BANK_ACCOUNT,
        nullable=False,
        index=True,
    )
    account_holder_name = Column(String(255), nullable=False)
    account_number = Column(String(50), nullable=True, index=True)
    ifsc_code = Column(String(20), nullable=True, index=True)
    bank_name = Column(String(255), nullable=True)
    branch_name = Column(String(255), nullable=True)
    upi_id = Column(String(100), nullable=True, index=True)

    is_primary = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    razorpay_contact_id = Column(String(255), nullable=True, index=True)
    razorpay_fund_account_id = Column(String(255), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("User", foreign_keys=[vendor_id])

