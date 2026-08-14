from app.schemas.response import PaginationResponse
from app.schemas.response import BaseResponse
from app.schemas.property_schema import PropertyCitySchema
from app.schemas.property_schema import PropertyLocationSchema

from typing import Optional

from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

class PropertyAssetSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    file_url: str | None = None
class PublicPropertyBase(BaseModel):
    
    name: str
    slug: str
    
    location: Optional[PropertyLocationSchema] = None
    city: Optional[PropertyCitySchema] = None
    type: Optional[str] = None
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    address: Optional[str] = None
    feature_image: Optional[PropertyAssetSchema] = None

class PublicPropertySchema(PublicPropertyBase):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )

class PublicPropertyResponse(BaseResponse):
    data: PublicPropertySchema


class PublicPropertyResponseListSchema(PaginationResponse):
    data: list[PublicPropertySchema]

