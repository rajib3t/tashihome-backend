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
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    PAID = "paid"
    FAILED = "failed"
    REVERSED = "reversed"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Payout(Base):
    __tablename__ = "payouts"
    __table_args__ = (
        CheckConstraint("amount > 0", name="chk_payouts_amount"),
        CheckConstraint("period_end >= period_start", name="chk_payouts_period"),
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
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    bank_account_id = Column(
        BigInteger,
        ForeignKey("vendor_bank_accounts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    gross_amount = Column(Numeric(12, 2), nullable=True)
    commission_amount = Column(Numeric(12, 2), nullable=True, default=0)
    amount = Column(Numeric(12, 2), nullable=False) # Net payout amount
    currency = Column(String(10), default="INR")
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    status = Column(
        Enum(PayoutStatus),
        default=PayoutStatus.PENDING,
        nullable=False,
        index=True,
    )
    mode = Column(String(20), default="NEFT") # NEFT, RTGS, IMPS, UPI
    transaction_id = Column(String(255), unique=True, nullable=True)
    razorpay_payout_id = Column(String(255), unique=True, nullable=True, index=True)
    razorpay_fund_account_id = Column(String(255), nullable=True)
    utr = Column(String(100), nullable=True) # Bank UTR
    failure_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    paid_at = Column(DateTime(timezone=True), nullable=True)

    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    vendor = relationship("User", foreign_keys=[vendor_id])
    bank_account = relationship("VendorBankAccount", foreign_keys=[bank_account_id])
    creator = relationship("User", foreign_keys=[created_by])
