import enum
import uuid

from app.core.database import Base

from sqlalchemy import UUID, BigInteger, Column, DateTime, Enum, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship
class RoomTypeStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class RoomType(Base):
    __tablename__ = "room_types"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    name = Column(String(255), unique=True, nullable=False, index=True)
    capacity = Column(Integer, nullable=False)
    status = Column(Enum(RoomTypeStatus), default=RoomTypeStatus.ACTIVE, nullable=False, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    property_room_types = relationship("PropertyRoomType", back_populates="room_type", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )