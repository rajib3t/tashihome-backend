from sqlalchemy import Column, BigInteger, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base

class PropertyRoomType(Base):
    __tablename__ = "property_room_types"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    property_id = Column(BigInteger, ForeignKey("properties.id", ondelete="CASCADE"), nullable=False, index=True)
    room_type_id = Column(BigInteger, ForeignKey("room_types.id", ondelete="CASCADE"), nullable=False, index=True)
    
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
    
    __table_args__ = (
        UniqueConstraint("property_id", "room_type_id", name="uq_property_room_type"),
    )
