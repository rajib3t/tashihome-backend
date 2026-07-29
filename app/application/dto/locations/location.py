from pydantic.dataclasses import dataclass
from pydantic import ConfigDict


@dataclass(config=ConfigDict(extra="forbid"))
class LocationDTO:
    name: str
    city_id: str

    