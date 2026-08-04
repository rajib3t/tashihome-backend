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


class PropertyFacility(Base):
    __tablename__ = "property_facilities"
    __table_args__ = (
        UniqueConstraint("property_id", "facility_id", name="uq_property_facility"),
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
    facility_id = Column(BigInteger, ForeignKey("facilities.id", ondelete="CASCADE"), nullable=False, index=True)
    quantity = Column(Integer, nullable=False, default=1)
    notes = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    property = relationship("Property", back_populates="property_facilities")
    facility = relationship("Facility")
