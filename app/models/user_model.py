import enum
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import UUID, BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String, func
from sqlalchemy.orm import foreign, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    VENDOR = "vendor"
    USER = "user"


class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),        # ✅ SQLAlchemy PostgreSQL type
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)
    full_name = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    is_profile_image_url = Column(String(500), default=None, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False, index=True)
    status = Column(Enum(UserStatus), default=UserStatus.INACTIVE, nullable=False, index=True)
    is_subscribed = Column(Boolean, default=False)
    is_terms_accepted = Column(Boolean, default=False)

    tokens = relationship("Token", back_populates="user", cascade="all, delete-orphan")
    login_logs = relationship("LoginLog", back_populates="user", cascade="all, delete-orphan")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    company = relationship(
        "Company",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
    )
    addresses = relationship(
        "Address",
        primaryjoin="and_(User.id==foreign(Address.owner_id), Address.owner_type=='user')",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings = relationship(
        "Booking",
        back_populates="guest",
        cascade="all, delete-orphan",
        foreign_keys="Booking.guest_id",
    )
