import uuid

from sqlalchemy import UUID, BigInteger, DateTime, ForeignKey, String, func
from app.core.database import Base
from sqlalchemy.orm import foreign, relationship
from sqlalchemy import Column

class Company(Base):

    __tablename__ = "companies"


    id = Column(BigInteger, primary_key=True, autoincrement=True)

    public_id = Column(
        UUID(as_uuid=True),
        default=uuid.uuid4,
        unique=True,
        nullable=False,
        index=True,
    )

    user_id = Column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name = Column(String(255), unique=True, nullable=False, index=True)

    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(20), unique=True, nullable=True, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    addresses = relationship(
        "Address",
        primaryjoin="and_(Company.id==foreign(Address.owner_id), Address.owner_type=='company')",
        back_populates="company",
        cascade="all, delete-orphan",
    )

    user = relationship(
        "User",
        back_populates="company",
        uselist=False,
    )

    @property
    def address(self):
        return self.addresses[0] if self.addresses else None
