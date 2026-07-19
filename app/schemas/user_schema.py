from typing import Optional
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse

from app.models.user_model import UserRole
class UserBase(BaseModel):
    email: str
    full_name: str
    phone: Optional[str] = None
    status: str
    role: UserRole
    is_profile_image_url : str | None = None
    
    

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "email": "john.doe@example.com",
                "full_name": "John Doe",
                "phone": "2345678900",
                "status": "active",
                "role": "user | admin | vendor",
                "is_profile_image_url": "https://example.com/profile.jpg"
            }
        }
    )


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




class UserBasicProfileResponse(BaseResponse):
    data: UserData
    
    

