from typing import Optional, Union
from fastapi import UploadFile
from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class FacilityDTO:
    name: str
    icon: Optional[Union[str, UploadFile]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "FACILITY_NAME")



@dataclass(config=ConfigDict(extra="forbid"))
class FacilityFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class FacilityQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[FacilityFilterDTO]] = None
