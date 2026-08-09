
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
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("vendor_id", "slug", name="uq_property_vendor_slug"),
        UniqueConstraint("vendor_id", "name", name="uq_property_vendor_name"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    vendor_id = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=False, index=True)
    location_id = Column(BigInteger, ForeignKey("locations.id", ondelete="SET NULL"), nullable=True, index=True)
    city_id = Column(BigInteger, ForeignKey("cities.id", ondelete="SET NULL"), nullable=True, index=True)
    room_type_id = Column(BigInteger, ForeignKey("room_types.id", ondelete="SET NULL"), nullable=True, index=True)

    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    latitude = Column(Numeric(10, 6), nullable=True)
    longitude = Column(Numeric(10, 6), nullable=True)
    price_per_night = Column(Numeric(12, 2), nullable=False, default=0)
    currency = Column(String(10), nullable=True, default="INR")
    sale_per_night = Column(Numeric(12, 2), nullable=True, default=0)
    is_featured = Column(Boolean, nullable=True, default=False)
    status = Column(Enum(PropertyStatus), default=PropertyStatus.DRAFT, nullable=False, index=True)

    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    vendor = relationship("User", foreign_keys=[vendor_id])
    location = relationship("Location")
    city = relationship("City")
    room_type = relationship("RoomType")

    property_assets = relationship(
        "PropertyAsset",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    property_facilities = relationship(
        "PropertyFacility",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    property_amenities = relationship(
        "PropertyAmenity",
        back_populates="property",
        cascade="all, delete-orphan",
    )
    property_food_options = relationship(
        "PropertyFoodOption",
        back_populates="property",
        cascade="all, delete-orphan",
    )
