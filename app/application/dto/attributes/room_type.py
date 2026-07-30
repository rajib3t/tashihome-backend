from typing import Optional

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class RoomTypeDTO:
    name: str
    capacity: int


class RoomTypeFilterDTO:
    name: str
    value: str


class RoomTypeQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[RoomTypeFilterDTO]] = None
