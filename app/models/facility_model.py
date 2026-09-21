import enum
import uuid

from sqlalchemy import BigInteger, Column, UUID, DateTime, Enum, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import relationship

from app.core.database import Base

class FacilityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Facility(Base):
    __tablename__ = "facilities"
    __table_args__ = (
        UniqueConstraint("vendor_id", "name", name="uq_facility_vendor_name"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), nullable=False, index=True)
    icon_url = Column(String(500), nullable=True)
    status = Column(Enum(FacilityStatus), default=FacilityStatus.ACTIVE, nullable=False, index=True)
    vendor_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    vendor = relationship("User", foreign_keys=[vendor_id])

    @property
    def is_global(self):
        return self.vendor_id is None

    @property
    def vendor_public_id(self):
        if "vendor" in self.__dict__:
            v = self.__dict__["vendor"]
            if v and getattr(v, "public_id", None):
                return str(v.public_id)
        try:
            from sqlalchemy.orm import inspect
            insp = inspect(self)
            if insp is not None and "vendor" not in insp.unloaded:
                v = getattr(self, "vendor", None)
                if v and getattr(v, "public_id", None):
                    return str(v.public_id)
        except Exception:
            pass
        return str(self.vendor_id) if self.vendor_id is not None else None
