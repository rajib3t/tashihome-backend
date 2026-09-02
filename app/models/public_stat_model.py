from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, JSON, String, func

from app.core.database import Base


class PublicStat(Base):
    __tablename__ = "public_stats"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    total_homes = Column(Integer, default=0, nullable=False)
    total_destinations = Column(Integer, default=0, nullable=False)
    verified_percent = Column(Integer, default=100, nullable=False)
    average_rating = Column(Float, default=4.9, nullable=False)
    total_reviews = Column(Integer, default=0, nullable=False)
    stats = Column(JSON, nullable=True)
    metadata_json = Column(JSON, nullable=True)

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

    def __repr__(self) -> str:
        return (
            f"<PublicStat(key='{self.key}', total_homes={self.total_homes}, "
            f"avg_rating={self.average_rating}, total_reviews={self.total_reviews})>"
        )

