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
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class TaxStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class TaxType(str, enum.Enum):
    PERCENTAGE = "percentage"
    FIXED = "fixed"


class Tax(Base):
    __tablename__ = "taxes"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False)
    code = Column(String(50), unique=True, nullable=False, index=True)
    rate = Column(Numeric(5, 2), nullable=False, default=0.0)
    tax_type = Column(
        Enum(TaxType),
        default=TaxType.PERCENTAGE,
        nullable=False,
    )
    is_inclusive = Column(Boolean, default=False, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)

    # GST compliance fields
    gst_number = Column(String(50), nullable=True)  # GSTIN
    legal_name = Column(String(255), nullable=True)  # Registered Legal Entity Name
    address = Column(Text, nullable=True)  # Registered Tax Address
    hsn_sac_code = Column(String(50), nullable=True)  # SAC code (e.g. 996311)

    # Component splits (optional / itemized GST)
    cgst_rate = Column(Numeric(5, 2), nullable=True)
    sgst_rate = Column(Numeric(5, 2), nullable=True)
    igst_rate = Column(Numeric(5, 2), nullable=True)

    description = Column(Text, nullable=True)
    status = Column(
        Enum(TaxStatus),
        default=TaxStatus.ACTIVE,
        nullable=False,
        index=True,
    )

    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    def __repr__(self) -> str:
        return f"<Tax(id={self.id}, code='{self.code}', rate={self.rate}, status='{self.status}')>"

