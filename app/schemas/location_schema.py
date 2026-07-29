from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import UUID

from typing import Optional

from app.schemas.city_schema import CitySchema
from app.schemas.response import BaseResponse, PaginationResponse

class LocationBase(BaseModel):
    name: str
    city: Optional[CitySchema] = None
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