from typing import Optional, Union
from fastapi import UploadFile
from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class CityDTO:
    name: str
    country_id: str
    image_url: Optional[Union[str, UploadFile]] = None


