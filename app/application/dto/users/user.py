from typing import Optional
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class UserDTO:
    full_name: str
    email: str
    phone: Optional[str] = None
    password: Optional[str] = None
   
    is_subscribed: Optional[bool] = False


@dataclass(config=ConfigDict(extra="forbid"))
class UserFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class UserQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    filters: Optional[list[UserFilterDTO]] = None


@dataclass(config=ConfigDict(extra="forbid"))
class UserUpdateDTO:
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_subscribed: Optional[bool] = None


@dataclass(config=ConfigDict(extra="forbid"))
class UserStatusUpdateDTO:
    status: str


@dataclass(config=ConfigDict(extra="forbid"))
class UserResetLinkDTO:
    confirm: str

