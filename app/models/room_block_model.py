import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class RoomBlock(Base):
    __tablename__ = "room_blocks"
    __table_args__ = (
        CheckConstraint("block_end_date > block_start_date", name="chk_room_block_dates"),
        CheckConstraint("units_blocked > 0", name="chk_room_block_units"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    property_id = Column(
        BigInteger,
        ForeignKey("properties.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    room_type_id = Column(
        BigInteger,
        ForeignKey("room_types.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    block_start_date = Column(Date, nullable=False)
    block_end_date = Column(Date, nullable=False)
    units_blocked = Column(Integer, nullable=False, default=1)
    reason = Column(String(255), nullable=True)

    created_by = Column(BigInteger, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    property = relationship("Property")
    room_type = relationship("RoomType")
    creator = relationship("User", foreign_keys=[created_by])
