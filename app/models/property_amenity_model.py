import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyAmenity(Base):
    __tablename__ = "property_amenities"
    __table_args__ = (
        UniqueConstraint("property_id", "amenity_id", name="uq_property_amenity"),
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
    amenity_id = Column(BigInteger, ForeignKey("amenities.id", ondelete="CASCADE"), nullable=False, index=True)
    notes = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    property = relationship("Property", back_populates="property_amenities")
    amenity = relationship("Amenity")
