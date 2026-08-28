from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass




@dataclass(config=ConfigDict(extra="forbid"))
class VendorDTO:
    full_name: str
    email: str
    phone: str

@dataclass(config=ConfigDict(extra="forbid"))
class VendorFilterDTO:
    name: str
    value: str
@dataclass(config=ConfigDict(extra="forbid"))
class VendorQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[VendorFilterDTO]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class VendorAddressUpdateDTO:
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None


@dataclass(config=ConfigDict(extra="forbid"))
class VendorCompanyUpdateDTO:
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[VendorAddressUpdateDTO] = None


@dataclass(config=ConfigDict(extra="forbid"))
class VendorUpdateDTO:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[VendorCompanyUpdateDTO] = None

@dataclass(config=ConfigDict(extra="forbid"))
class VendorResetLinkDTO:
    confirm:str
