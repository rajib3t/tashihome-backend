from fastapi import UploadFile
from typing import List, Optional

from pydantic import AliasChoices, ConfigDict, Field, field_validator
from pydantic.dataclasses import dataclass

from app.core.exceptions import AppException
from app.utils.validation import validate_description


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyFilterDTO:
    name: str
    value: str


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyQueryDTO:
    page: int = 1
    size: int = 10
    sort_by: str = "created_at"
    sort_order: str = "desc"
    name: Optional[str] = None
    slug: Optional[str] = None
    vendor_id: Optional[int] = None
    location_id: Optional[int] = None
    city_id: Optional[int] = None
    status: Optional[str] = None
    filters: Optional[list[PropertyFilterDTO]] = None

    @field_validator("page", "size")
    @classmethod
    def validate_positive(cls, value):
        if value < 1:
            raise AppException(
                status_code=422,
                message="Page and size must be greater than 0.",
                field="page",
                error_code="PAGINATION_INVALID",
            )
        return value

    @field_validator("sort_order")
    @classmethod
    def validate_sort_order(cls, value):
        if value not in ["asc", "desc"]:
            raise AppException(
                status_code=422,
                message="Sort order must be 'asc' or 'desc'.",
                field="sort_order",
                error_code="SORT_ORDER_INVALID",
            )
        return value


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyAddressDTO:
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "India"


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyGeolocationDTO:
    latitude: Optional[float] = None
    longitude: Optional[float] = None


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyDTO:
    name: str
    vendor: Optional[str] = None
    type: Optional[str] = None
    slug: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    address: Optional[object] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    manual_address: Optional[object] = None
    address_details: Optional[object] = None
    geolocation: Optional[object] = None
    latitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("latitude", "lat"))
    longitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("longitude", "lon"))
    main_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    max_guests: Optional[int] = None
    vendor_id: Optional[str] = None
    location_id: Optional[str] = None
    city_id: Optional[str] = None
    room_type_id: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_per_night: Optional[float] = None
    sale_price: Optional[float] = None
    sale_per_night: Optional[float] = None
    is_featured: Optional[bool] = None
    status: Optional[str] = None
    amenity_ids: Optional[List[str]] = None
    facility_ids: Optional[List[str]] = None
    room_type_ids: Optional[List[str]] = None
    food_option_ids: Optional[List[str]] = None
    amenities: Optional[List["PropertyAmenitiesDTO"]] = None
    facility: Optional[List["PropertyFacilityDTO"]] = None
    facilities: Optional[List["PropertyFacilityDTO"]] = None
    room_types: Optional[List["PropertyRoomTypeDTO"]] = None
    food_options: Optional[List["FoodOptionDTO"]] = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value):
        from app.utils.validation import validate_name_field
        return validate_name_field(value, "name", 50, "PROPERTY_NAME")

    @field_validator("description")
    @classmethod
    def validate_description(cls, value):
        if value is None:
            return value
        from app.utils.validation import validate_description
        return validate_description(value, required=False, max_words=150, max_length=2000)

    @field_validator("vendor", "type", "city", "location", "address")
    @classmethod
    def validate_text_fields(cls, value):
        if value is None:
            return value
        if isinstance(value, str):
            value = value.strip()
            return value or None
        return value

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, value):
        if value is not None:
            try:
                val = float(value)
            except (ValueError, TypeError):
                raise AppException(
                    status_code=422,
                    message="Latitude must be a valid number.",
                    field="latitude",
                    error_code="LATITUDE_INVALID",
                )
            if not (-90.0 <= val <= 90.0):
                raise AppException(
                    status_code=422,
                    message="Latitude must be between -90.0 and 90.0.",
                    field="latitude",
                    error_code="LATITUDE_OUT_OF_RANGE",
                )
            return val
        return None

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, value):
        if value is not None:
            try:
                val = float(value)
            except (ValueError, TypeError):
                raise AppException(
                    status_code=422,
                    message="Longitude must be a valid number.",
                    field="longitude",
                    error_code="LONGITUDE_INVALID",
                )
            if not (-180.0 <= val <= 180.0):
                raise AppException(
                    status_code=422,
                    message="Longitude must be between -180.0 and 180.0.",
                    field="longitude",
                    error_code="LONGITUDE_OUT_OF_RANGE",
                )
            return val
        return None

    @field_validator("slug")
    @classmethod
    def validate_slug_field(cls, value):
        if value is None:
            return value
        value = value.strip()
        return value or None



@dataclass(config=ConfigDict(extra="ignore"))
class PropertyAmenitiesDTO:
    id: Optional[str] = None
    amenity_id: Optional[str] = None
    amenity: Optional[dict] = None


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyFacilityDTO:
    id: Optional[str] = None
    facility_id: Optional[str] = None
    facility: Optional[dict] = None


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyRoomTypePriceDTO:
    id: Optional[str] = None
    occupancy: int = 1
    price_per_night: float = 0.0
    sale_per_night: Optional[float] = 0.0


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyRoomTypeDTO:
    id: Optional[str] = None
    room_type_id: Optional[str] = None
    total_units: Optional[int] = 1
    price_per_night: Optional[float] = None
    sale_per_night: Optional[float] = None
    pricing_tiers: Optional[List[PropertyRoomTypePriceDTO]] = None
    room_type: Optional[dict] = None


@dataclass(config=ConfigDict(extra="ignore"))
class FoodOptionDTO:
    id: Optional[str] = None
    name: Optional[str] = None
    is_included: Optional[bool] = None
    allow: bool = True


@dataclass(config=ConfigDict(extra="ignore"))
class PropertyUpdateDTO(PropertyDTO):
    name: Optional[str] = None
    vendor: Optional[str] = None
    type: Optional[str] = None
    slug: Optional[str] = None
    city: Optional[str] = None
    location: Optional[str] = None
    address: Optional[object] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    manual_address: Optional[object] = None
    address_details: Optional[object] = None
    geolocation: Optional[object] = None
    latitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("latitude", "lat"))
    longitude: Optional[float] = Field(default=None, validation_alias=AliasChoices("longitude", "lon"))
    main_image_url: Optional[str] = None
    cover_image_url: Optional[str] = None
    max_guests: Optional[int] = None
    vendor_id: Optional[str] = None
    location_id: Optional[str] = None
    city_id: Optional[str] = None
    room_type_id: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    price_per_night: Optional[float] = None
    sale_price: Optional[float] = None
    sale_per_night: Optional[float] = None
    currency: Optional[str] = None
    amenities: Optional[List[PropertyAmenitiesDTO]] = None
    facility: Optional[List[PropertyFacilityDTO]] = None
    facilities: Optional[List[PropertyFacilityDTO]] = None
    room_types: Optional[List[PropertyRoomTypeDTO]] = None
    food_options: Optional[List[FoodOptionDTO]] = None
    status: Optional[str] = None

    
@dataclass(config=ConfigDict(extra="forbid"))
class AssetsDTO:
    name: str 
    file: Optional[UploadFile] = None


@dataclass(config=ConfigDict(extra="forbid"))
class PropertyAssetsDTO:
    gallery_images: Optional[List[AssetsDTO]] = None
    feature_image: Optional[AssetsDTO] = None
    cover_image: Optional[AssetsDTO] = None


def extract_property_address_and_geo(
    dto: object,
) -> tuple[Optional[str], Optional[dict], Optional[float], Optional[float]]:
    """
    Extracts (address_str, manual_address_dict, latitude, longitude)
    from property DTO.
    """
    # 1. Geolocation
    lat = getattr(dto, "latitude", None)
    lon = getattr(dto, "longitude", None)
    geo = getattr(dto, "geolocation", None)
    if geo is not None:
        if isinstance(geo, dict):
            if lat is None:
                lat = geo.get("latitude") if "latitude" in geo else geo.get("lat")
            if lon is None:
                lon = geo.get("longitude") if "longitude" in geo else geo.get("lon")
        else:
            if lat is None:
                lat = getattr(geo, "latitude", None)
            if lon is None:
                lon = getattr(geo, "longitude", None)

    lat_float = None
    if lat is not None:
        lat_float = float(lat)
        if not (-90.0 <= lat_float <= 90.0):
            raise AppException(
                status_code=422,
                message="Latitude must be between -90.0 and 90.0.",
                field="latitude",
                error_code="LATITUDE_OUT_OF_RANGE",
            )

    lon_float = None
    if lon is not None:
        lon_float = float(lon)
        if not (-180.0 <= lon_float <= 180.0):
            raise AppException(
                status_code=422,
                message="Longitude must be between -180.0 and 180.0.",
                field="longitude",
                error_code="LONGITUDE_OUT_OF_RANGE",
            )

    # 2. Manual address
    line1 = getattr(dto, "address_line1", None)
    line2 = getattr(dto, "address_line2", None)
    postal = getattr(dto, "postal_code", None)
    country = getattr(dto, "country", None) or "India"

    nested = getattr(dto, "manual_address", None) or getattr(dto, "address_details", None)
    if nested:
        if isinstance(nested, dict):
            line1 = line1 or nested.get("address_line1")
            line2 = line2 or nested.get("address_line2")
            postal = postal or nested.get("postal_code")
            country = nested.get("country") or country
        else:
            line1 = line1 or getattr(nested, "address_line1", None)
            line2 = line2 or getattr(nested, "address_line2", None)
            postal = postal or getattr(nested, "postal_code", None)
            country = getattr(nested, "country", None) or country

    addr_val = getattr(dto, "address", None)
    addr_str = None
    if isinstance(addr_val, dict):
        line1 = line1 or addr_val.get("address_line1")
        line2 = line2 or addr_val.get("address_line2")
        postal = postal or addr_val.get("postal_code")
        country = addr_val.get("country") or country
    elif addr_val and not isinstance(addr_val, str):
        line1 = line1 or getattr(addr_val, "address_line1", None)
        line2 = line2 or getattr(addr_val, "address_line2", None)
        postal = postal or getattr(addr_val, "postal_code", None)
        country = getattr(addr_val, "country", None) or country
    elif isinstance(addr_val, str) and addr_val.strip():
        addr_str = addr_val.strip()

    manual_dict = None
    if line1 or postal or addr_str:
        if not line1 and addr_str:
            line1 = addr_str

        manual_dict = {
            "address_line1": (line1 or "").strip(),
            "address_line2": line2.strip() if line2 else None,
            "postal_code": (postal or "000000").strip(),
            "country": (country or "India").strip(),
        }

        if not addr_str:
            parts = [manual_dict["address_line1"]]
            if manual_dict["address_line2"]:
                parts.append(manual_dict["address_line2"])
            if manual_dict["postal_code"] and manual_dict["postal_code"] != "000000":
                parts.append(manual_dict["postal_code"])
            if manual_dict["country"]:
                parts.append(manual_dict["country"])
            addr_str = ", ".join(parts)

    return addr_str, manual_dict, lat_float, lon_float