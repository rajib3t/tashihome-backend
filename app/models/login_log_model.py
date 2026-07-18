from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    func,
)

from sqlalchemy.orm import relationship

from app.core.database import Base


class LoginLog(Base):
    __tablename__ = "login_logs"

    id = Column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        index=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    ip_address = Column(String(100), nullable=False)
    city = Column(String(100))
    country = Column(String(100))
    device_info = Column(JSONB, nullable=False)
    user_agent = Column(String(1024))

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user = relationship(
        "User",
        back_populates="login_logs",
    )