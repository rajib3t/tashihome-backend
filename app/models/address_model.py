import uuid

from sqlalchemy import UUID, BigInteger, Column, DateTime, String, func

from app.core.database import Base
from sqlalchemy.orm import relationship

class Address(Base):
    __tablename__ = "addresses"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )


    owner_type = Column(String(50), nullable=False)  # e.g., 'user', 'company'
    owner_id = Column(BigInteger, nullable=False)  # ID of the user or company


    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255), nullable=True)
    postal_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

  

    # Relationships
    user = relationship(
        "User",
        primaryjoin="and_(Address.owner_id==User.id, Address.owner_type=='user')",
        back_populates="addresses",
    )

    company = relationship(
        "Company",
        primaryjoin="and_(Address.owner_id==Company.id, Address.owner_type=='company')",
        back_populates="addresses",
    )