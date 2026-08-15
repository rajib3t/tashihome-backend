from pydantic import AliasChoices, BaseModel, Field, field_validator
from sqlalchemy import UUID

from app.schemas.country_schema import CountrySchema
from app.schemas.response import PaginationResponse


class CityBase(BaseModel):
    name: str
    country: CountrySchema | None = None
    image_url: str | None = None
    tag_line: str | None = None
    short_description: str | None = None
    is_featured: bool | None = None
    status: str

    


class CitySchema(CityBase):
    

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


class CityResponseSchema(BaseModel):
    data: CitySchema

class CityListResponseSchema(PaginationResponse):
    data: list[CitySchema]