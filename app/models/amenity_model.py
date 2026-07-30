import uuid

import enum
from sqlalchemy import UUID, BigInteger, Column, DateTime, Enum, ForeignKey, String, func

from app.core.database import Base

class AmenityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Amenity(Base):
    __tablename__ = "amenities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), unique=True, nullable=False, index=True)
    icon_url = Column(String(500), nullable=True)
    status = Column(Enum(AmenityStatus), default=AmenityStatus.ACTIVE, nullable=False, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )