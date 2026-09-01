from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.response import BaseResponse


class PublicStatItemSchema(BaseModel):
    key: str
    target: float
    current: float = 0.0
    suffix: Optional[str] = None
    decimals: Optional[int] = 0
    label: str
    model_config = ConfigDict(from_attributes=True)


class PublicStatsDataSchema(BaseModel):
    total_homes: int = 0
    total_destinations: int = 0
    verified_percent: int = 100
    average_rating: float = 4.9
    total_reviews: int = 0
    stats: List[PublicStatItemSchema] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class PublicStatsResponseSchema(BaseResponse):
    data: PublicStatsDataSchema

