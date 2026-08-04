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
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyFoodOptionStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PropertyFoodOption(Base):
    __tablename__ = "property_food_options"
    __table_args__ = (
        UniqueConstraint("property_id", "name", name="uq_property_food_option_name"),
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
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_included = Column(Boolean, nullable=False, default=False)
    status = Column(Enum(PropertyFoodOptionStatus), default=PropertyFoodOptionStatus.ACTIVE, nullable=False, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    property = relationship("Property", back_populates="property_food_options")
