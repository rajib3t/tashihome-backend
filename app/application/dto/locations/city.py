from typing import Optional, Union
from fastapi import UploadFile
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class CityDTO:
    name: str
    country_id: str
    image_url: Optional[Union[str, UploadFile]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class CityFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class CityQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    country_id: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[CityFilterDTO]] = None