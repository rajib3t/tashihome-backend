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


class PropertyRoomTypePrice(Base):
    """
    Stores variable pricing for a property room type based on guest occupancy / capacity.
    E.g. A 4-bedded room:
    - occupancy: 1 -> price_per_night: 1500
    - occupancy: 2 -> price_per_night: 2200
    - occupancy: 3 -> price_per_night: 2800
    - occupancy: 4 -> price_per_night: 3500
    """
    __tablename__ = "property_room_type_prices"
    __table_args__ = (
        UniqueConstraint(
            "property_room_type_id",
            "occupancy",
            name="uq_property_room_type_price_occupancy",
        ),
        CheckConstraint("occupancy > 0", name="chk_room_price_occupancy"),
        CheckConstraint("price_per_night >= 0", name="chk_room_price_positive"),
        CheckConstraint("sale_per_night >= 0", name="chk_room_sale_price_positive"),
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
    occupancy = Column(
        Integer,
        nullable=False,
        comment="Number of guests this price tier applies to (1, 2, 3, 4, etc.)",
    )
    price_per_night = Column(
        Numeric(12, 2),
        nullable=False,
        default=0,
        comment="Standard nightly price for this occupancy count",
    )
    sale_per_night = Column(
        Numeric(12, 2),
        nullable=True,
        default=0,
        comment="Discounted nightly price for this occupancy count",
    )

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    property_room_type = relationship("PropertyRoomType", back_populates="pricing_tiers")

