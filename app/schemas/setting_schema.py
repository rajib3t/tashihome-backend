from typing import List, Optional

from pydantic import BaseModel

from app.schemas.response import BaseResponse


class SettingSchema(BaseModel):
    name: str
    value: Optional[str] = None


class SettingResponseSchema(BaseResponse):
    data: List[SettingSchema]