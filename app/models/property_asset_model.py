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
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class PropertyAssetType(str, enum.Enum):
    IMAGE = "image"
    VIDEO = "video"
    DOCUMENT = "document"


class PropertyAssetStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"


class PropertyAsset(Base):
    __tablename__ = "property_assets"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    asset_type = Column(Enum(PropertyAssetType), default=PropertyAssetType.IMAGE, nullable=False, index=True)
    file_url = Column(String(500), nullable=False)
    title = Column(String(255), nullable=True)
    is_primary = Column(Boolean, nullable=False, default=False)
    sort_order = Column(Integer, nullable=False, default=0)
    status = Column(Enum(PropertyAssetStatus), default=PropertyAssetStatus.ACTIVE, nullable=False, index=True)

    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    updated_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    property = relationship("Property", back_populates="property_assets")
