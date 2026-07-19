from typing import List

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class SettingSchema(BaseModel):
    
    name: str
    value: str


class SettingResponseSchema(BaseResponse):
    data: List[SettingSchema]