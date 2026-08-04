from sqlalchemy import UUID, BigInteger, Column, DateTime, Enum, ForeignKey, String, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base
import enum
import uuid

class LocationStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
class Location(Base):
    __tablename__ = "locations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    # remove unique=True here, keep index for lookup speed
    name = Column(String(255), nullable=False, index=True)

    image_url = Column(String(500), nullable=True)
    city_id = Column(
        BigInteger,
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    status = Column(Enum(LocationStatus), default=LocationStatus.ACTIVE, nullable=False, index=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    city = relationship("City", back_populates="locations")

    __table_args__ = (
        UniqueConstraint("city_id", "name", name="uq_location_city_name"),
    )

    properties = relationship(
        "Property",
        back_populates="location",
        cascade="all, delete-orphan",
    )