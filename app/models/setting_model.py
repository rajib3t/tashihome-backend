from sqlalchemy import BigInteger, Column, DateTime, String, Text, func

from app.core.database import Base


class Setting(Base):
    __tablename__ = 'settings'

    id = Column(BigInteger, primary_key=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=False)

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


    def __repr__(self):
        return f"<Setting(key='{self.key}', value='{self.value}')>"
    
    