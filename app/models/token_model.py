import enum

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Enum, ForeignKey, String, func

from app.core.database import Base

from sqlalchemy.orm import relationship

class TokenType(str, enum.Enum):
    ACCESS = "access_token"
    REFRESH = "refresh_token"
    PASSWORD_RESET = "password_reset_token"
    EMAIL_VERIFICATION = "email_verification_token"

class Token(Base):
    __tablename__ = "tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(
        BigInteger,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    type = Column(Enum(TokenType), nullable=True)
    token = Column(String(1000), unique=True, nullable=False, index=True)
    is_revoked = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False) 


    user = relationship(
        "User",
        back_populates="tokens",
    )
    