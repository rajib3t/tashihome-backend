from typing import Optional

from pydantic import ConfigDict, field_validator
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class CreateVendorDTO:
    full_name: str
    email: str
    phone: str
    