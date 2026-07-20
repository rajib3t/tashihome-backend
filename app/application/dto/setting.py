from datetime import datetime
from typing import Optional, Union

from fastapi import UploadFile
from pydantic import BaseModel, ConfigDict, field_validator


class SettingUpdateDTO(BaseModel):
    model_config = ConfigDict(extra="forbid")
    app_name: Optional[str] = None
    app_logo: Optional[Union[str, UploadFile]] = None
    white_logo: Optional[Union[str, UploadFile]] = None
    app_favicon: Optional[Union[str, UploadFile]] = None
    app_timezone: Optional[str] = None
    app_date_format: Optional[str] = None
    app_time_format: Optional[str] = None
    is_enabled_coming_soon: Optional[str] = None
    launch_date:Optional[datetime]=None
    coming_soon_message: Optional[str] = None
    coming_background_image: Optional[Union[str, UploadFile]] = None
    coming_soon_video: Optional[Union[str, UploadFile]] = None

    @field_validator('is_enabled_coming_soon', mode='before')
    @classmethod
    def convert_bool_to_str(cls, v):
        if isinstance(v, bool):
            return str(v).lower()
        return v
