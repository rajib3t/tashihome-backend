from typing import Optional, Union

from fastapi import UploadFile
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class AmenityDTO:
    name: str
    icon: Optional[Union[str, UploadFile]] = None


class AmenityFilterDTO:
    name: str
    value: str


class AmenityQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[AmenityFilterDTO]] = None
