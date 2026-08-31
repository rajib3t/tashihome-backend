from typing import Optional

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class CreateHostRequestDTO:
    full_name: str
    email: str
    phone: str
    company_name: Optional[str] = None
    property_name: Optional[str] = None
    property_type: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    expected_rooms: Optional[int] = None
    notes: Optional[str] = None


@dataclass(config=ConfigDict(extra="forbid"))
class HostRequestFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class HostRequestQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    search: Optional[str] = None
    status: Optional[str] = None
    city: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    filters: Optional[list[HostRequestFilterDTO]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class UpdateHostRequestStatusDTO:
    status: str
    notes: Optional[str] = None


@dataclass(config=ConfigDict(extra="forbid"))
class AddHostRequestMessageDTO:
    message: str
    is_internal: bool = False


@dataclass(config=ConfigDict(extra="forbid"))
class ConvertHostRequestDTO:
    company_name: Optional[str] = None
    company_email: Optional[str] = None
    company_phone: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    temporary_password: Optional[str] = None


@dataclass(config=ConfigDict(extra="forbid"))
class BecomeHostDTO:
    company_name: str
    address_line1: str
    postal_code: str
    country: str
    company_email: Optional[str] = None
    company_phone: Optional[str] = None
    address_line2: Optional[str] = None
    full_name: Optional[str] = None
    phone: Optional[str] = None


