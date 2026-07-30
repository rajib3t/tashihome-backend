from typing import Optional, Union
from fastapi import UploadFile
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class FacilityDTO:
    name: str
    icon: Optional[Union[str, UploadFile]] = None