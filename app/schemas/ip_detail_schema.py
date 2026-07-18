from typing import List, Optional
from pydantic import BaseModel


class IpDetailResponse(BaseModel):
    ipVersion: Optional[int] = None
    ipAddress: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    countryName: Optional[str] = None
    countryCode: Optional[str] = None
    capital: Optional[str] = None
    phoneCodes: List[int] = []
    timeZones: List[str] = []
    zipCode: Optional[str] = None
    cityName: Optional[str] = None
    regionName: Optional[str] = None
    regionCode: Optional[str] = None
    continent: Optional[str] = None
    continentCode: Optional[str] = None
    currencies: List[str] = []
    languages: List[str] = []
    asn: Optional[str] = None
    asnOrganization: Optional[str] = None
    isProxy: Optional[bool] = None