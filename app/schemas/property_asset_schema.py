from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.response import BaseResponse


class PropertyAssetSchema(BaseModel):
    id: UUID | str | None = Field(
        default=None,
        validation_alias=AliasChoices("public_id", "id"),
        serialization_alias="id",
    )
    property_id: int | None = None
    asset_type: str | None = None
    file_url: str | None = None
    title: str | None = None
    is_primary: bool | None = None
    sort_order: int | None = None
    status: str | None = None
    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def validate_public_id(cls, value):
        if value is None:
            return None
        if isinstance(value, UUID):
            return str(value)
        return str(value)


class PropertyAssetResponseSchema(BaseResponse):
    data: list[PropertyAssetSchema]
