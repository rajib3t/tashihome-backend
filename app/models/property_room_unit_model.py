import enum
import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoomUnitStatus(str, enum.Enum):
    ACTIVE = "active"
    MAINTENANCE = "maintenance"
    INACTIVE = "inactive"


class PropertyRoomUnit(Base):
    __tablename__ = "property_room_units"
    __table_args__ = (
        UniqueConstraint("property_room_type_id", "unit_identifier", name="uq_property_room_unit"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    property_room_type_id = Column(
        BigInteger,
        ForeignKey("property_room_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    unit_identifier = Column(String(100), nullable=False)
    status = Column(
        Enum(RoomUnitStatus),
        default=RoomUnitStatus.ACTIVE,
        nullable=False,
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
    property_room_type = relationship("PropertyRoomType", back_populates="property_room_units")
