from typing import Optional
from uuid import UUID
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from app.schemas.response import BaseResponse, PaginationResponse
from app.schemas.public.property_schema import (
    PropertyAssetSchema,
    PropertyCitySchema,
    PropertyLocationSchema,
    PropertyRoomTypeSchema,
    PropertyAmenitySchema,
    PropertyFacilitySchema,
    PropertyFoodOptionSchema,
    PublicPropertyDetailResponse,
    PublicPropertySchema,
)


class PublicStaySchema(PublicPropertySchema):
    pass


class PublicStayDetailResponse(PublicPropertyDetailResponse):
    pass


class PublicStayResponse(BaseResponse):
    data: PublicStayDetailResponse


class PublicStaySearchResponseSchema(PaginationResponse):
    data: list[PublicStaySchema]


class PublicStayListResponseSchema(PaginationResponse):
    data: list[PublicStaySchema]

