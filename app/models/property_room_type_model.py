import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyRoomType(Base):
    __tablename__ = "property_room_types"
    __table_args__ = (
        UniqueConstraint("property_id", "room_type_id", name="uq_property_room_type"),
        CheckConstraint("total_units > 0", name="chk_property_room_type_units"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    room_type_id = Column(BigInteger, ForeignKey("room_types.id", ondelete="CASCADE"), nullable=False, index=True)
    total_units = Column(Integer, nullable=False, default=1, server_default="1")
    price_per_night = Column(Numeric(12, 2), nullable=True, default=0, comment="Base price per night for this room type")
    sale_per_night = Column(Numeric(12, 2), nullable=True, default=0, comment="Sale price per night for this room type")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    property = relationship("Property", back_populates="property_room_types")
    room_type = relationship("RoomType", back_populates="property_room_types")
    property_room_units = relationship(
        "PropertyRoomUnit",
        back_populates="property_room_type",
        cascade="all, delete-orphan",
    )
    pricing_tiers = relationship(
        "PropertyRoomTypePrice",
        back_populates="property_room_type",
        cascade="all, delete-orphan",
        order_by="PropertyRoomTypePrice.occupancy",
    )
