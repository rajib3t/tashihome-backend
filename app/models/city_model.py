import enum
import uuid

from sqlalchemy import UUID, BigInteger, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base

class CityStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class City(Base):
    __tablename__ = "cities"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(String(255), unique=True, nullable=False, index=True)
    image_url = Column(String(500), nullable=True)
    country_id = Column(
        BigInteger,
        ForeignKey("countries.id", ondelete="CASCADE"),
        nullable=False,
        
        )
    
    status = Column(Enum(CityStatus), default=CityStatus.ACTIVE, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    # Relationships
    country = relationship(
        "Country", 
        back_populates="cities",
    )

    locations = relationship(
        "Location",
        back_populates="city",
        cascade="all, delete-orphan",
    )
