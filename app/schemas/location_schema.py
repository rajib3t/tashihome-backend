from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import UUID

from typing import Optional

from app.schemas.country_schema import CountrySchema
from app.schemas.response import BaseResponse, PaginationResponse

class CityLocationSchema(BaseModel):
    name: str
    country: CountrySchema | None = None
    status: str
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class LocationBase(BaseModel):
    name: str
    city: Optional[CityLocationSchema] = None
    status: str 

class LocationSchema(LocationBase):
    id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)
    


class LocationResponseSchema(BaseResponse):
    data: LocationSchema

class LocationsResponseSchema(PaginationResponse):
    data: list[LocationSchema]
