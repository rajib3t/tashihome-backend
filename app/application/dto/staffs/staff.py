from typing import Optional
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.models.user_model import UserRole


@dataclass(config=ConfigDict(extra="forbid"))
class StaffDTO:
    full_name: str
    email: str
    role: Optional[UserRole] = UserRole.STAFF
    phone: Optional[str] = None
    password: Optional[str] = None
    is_subscribed: Optional[bool] = False


@dataclass(config=ConfigDict(extra="forbid"))
class StaffFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class StaffQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    role: Optional[str] = None
    filters: Optional[list[StaffFilterDTO]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class StaffUpdateDTO:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[UserRole] = None
    is_subscribed: Optional[bool] = None


@dataclass(config=ConfigDict(extra="forbid"))
class StaffStatusUpdateDTO:
    status: str


@dataclass(config=ConfigDict(extra="forbid"))
class StaffResetLinkDTO:
    confirm: str

