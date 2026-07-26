import enum
import uuid

from sqlalchemy import UUID, BigInteger, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base

class CountryStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Country(Base):
    
    __tablename__ = "countries"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    name = Column(String(255), unique=True, nullable=False, index=True)

    code = Column(String(10), unique=True, nullable=False, index=True)

    status = Column(Enum(CountryStatus), default=CountryStatus.ACTIVE, nullable=False, index=True)

    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


    # Relationships
    cities = relationship(
        "City", 
        back_populates="country",
        cascade="all, delete-orphan"
    )

    
