from typing import Optional

from pydantic.dataclasses import dataclass
from pydantic import ConfigDict, field_validator


@dataclass(config=ConfigDict(extra="forbid"))
class LocationDTO:
    name: str
    city_id: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "LOCATION_NAME")


@dataclass(config=ConfigDict(extra="forbid"))
class UpdateLocationDTO:
    name: str
    city_id: str

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "LOCATION_NAME")



@dataclass(config=ConfigDict(extra="forbid"))
class LocationStatusDTO:
    status: str

@dataclass(config=ConfigDict(extra="forbid"))
class LocationFilterDTO:
    name: str
    value: str
@dataclass(config=ConfigDict(extra="forbid"))
class LocationQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    city_id: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[LocationFilterDTO]] = None
