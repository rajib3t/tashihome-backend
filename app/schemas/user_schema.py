from typing import Optional
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    status: str
    role: str 
    is_profile_image_url : str | None = None
    
    

    model_config = ConfigDict(from_attributes=True)


class UserData(UserBase):
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