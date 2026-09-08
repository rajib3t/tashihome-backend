import json
import logging
from typing import Any, List, Optional

from app.mcp.protocol import ReadResourceResult, Resource, ResourceContent

logger = logging.getLogger(__name__)

STATIC_RESOURCES: List[Resource] = [
    Resource(
        uri="tashihome://destinations",
        name="Homestay Destinations",
        description="List of top cities and popular tourist hubs with homestays directly from database.",
        mimeType="application/json",
    ),
    Resource(
        uri="tashihome://featured-cities",
        name="Featured Cities",
        description="List of featured cities and travel destinations directly from database.",
        mimeType="application/json",
    ),
    Resource(
        uri="tashihome://cancellation-policies",
        name="Platform Cancellation Policies",
        description="Standard cancellation policies and refund rules on TashiHome.",
        mimeType="application/json",
    ),
    Resource(
        uri="tashihome://booking-guide",
        name="Guest Booking and Registration Guide",
        description="Guidelines on guest booking, check-in policies, and auto-registration requirements.",
        mimeType="application/json",
    ),
]


class MCPResourceHandler:
    def __init__(
        self,
        city_service: Optional[Any] = None,
        country_service: Optional[Any] = None,
        property_service: Optional[Any] = None,
    ):
        self.city_service = city_service
        self.country_service = country_service
        self.property_service = property_service

    async def list_resources(self) -> List[Resource]:
        resources = list(STATIC_RESOURCES)
        return resources

    async def _resolve_country_name(self, country_obj: Any = None) -> Optional[str]:
        if country_obj and hasattr(country_obj, "name") and country_obj.name:
            return country_obj.name
        if self.country_service:
            try:
                countries = await self.country_service.get_all()
                if countries:
                    c0 = countries[0]
                    return getattr(c0, "name", None)
            except Exception:
                pass
        return None

    async def read_resource(self, uri: str) -> ReadResourceResult:
        if uri in ("tashihome://destinations", "tashihome://featured-cities", "tashihome://cities"):
            # 1. Fetch live featured or active cities from database if city_service is configured
            if self.city_service:
                try:
                    db_cities = []
                    if hasattr(self.city_service, "get_city_with_is_featured"):
                        try:
                            db_cities = await self.city_service.get_city_with_is_featured(with_relations={"country": True})
                        except Exception:
                            db_cities = []
                    
                    if not db_cities:
                        all_res = await self.city_service.get_all()
                        db_cities = getattr(all_res, "items", all_res) or []

                    if db_cities:
                        data = []
                        for c in db_cities:
                            country_str = await self._resolve_country_name(getattr(c, "country", None))
                            data.append({
                                "id": str(getattr(c, "public_id", c.id)),
                                "name": c.name,
                                "slug": c.slug,
                                "tag_line": getattr(c, "tag_line", None),
                                "short_description": getattr(c, "short_description", None),
                                "image_url": getattr(c, "image_url", None),
                                "is_featured": bool(getattr(c, "is_featured", False)),
                                "country": country_str,
                            })
                        return ReadResourceResult(
                            contents=[
                                ResourceContent(
                                    uri=uri,
                                    mimeType="application/json",
                                    text=json.dumps(data, indent=2),
                                )
                            ]
                        )
                except Exception as e:
                    logger.warning("Error fetching featured cities from database for MCP resource '%s': %s", uri, e)

            return ReadResourceResult(
                contents=[
                    ResourceContent(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps([], indent=2),
                    )
                ]
            )

        elif (uri.startswith("tashihome://cities/") or uri.startswith("tashihome://destinations/")) and self.city_service:
            slug = uri.split("/")[-1].strip()
            city = None
            try:
                city = await self.city_service.get_by_slug(slug, with_relations={"country": True})
                if not city:
                    city = await self.city_service.get_by_name(slug, with_relations={"country": True})
            except Exception as e:
                logger.warning("Error fetching city '%s' from database: %s", slug, e)

            if city:
                country_str = await self._resolve_country_name(getattr(city, "country", None))
                city_data = {
                    "id": str(getattr(city, "public_id", city.id)),
                    "name": city.name,
                    "slug": city.slug,
                    "tag_line": getattr(city, "tag_line", None),
                    "short_description": getattr(city, "short_description", None),
                    "image_url": getattr(city, "image_url", None),
                    "is_featured": bool(getattr(city, "is_featured", False)),
                    "country": country_str,
                }
                return ReadResourceResult(
                    contents=[
                        ResourceContent(
                            uri=uri,
                            mimeType="application/json",
                            text=json.dumps(city_data, indent=2),
                        )
                    ]
                )

        elif uri == "tashihome://cancellation-policies":
            data = {
                "flexible": "Full refund up to 24 hours prior to check-in.",
                "moderate": "Full refund up to 5 days before check-in.",
                "strict": "50% refund up to 7 days before check-in. No refund after 7 days.",
            }
            return ReadResourceResult(
                contents=[
                    ResourceContent(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps(data, indent=2),
                    )
                ]
            )

        elif uri == "tashihome://booking-guide":
            data = {
                "rules": [
                    "Valid government ID required at check-in.",
                    "Check-in time: 14:00 onwards; Check-out time: 11:00 AM.",
                    "Unregistered guests will have accounts created upon checkout with booking confirmation sent to email.",
                ]
            }
            return ReadResourceResult(
                contents=[
                    ResourceContent(
                        uri=uri,
                        mimeType="application/json",
                        text=json.dumps(data, indent=2),
                    )
                ]
            )

        elif uri.startswith("tashihome://stays/") and self.property_service:
            slug = uri.replace("tashihome://stays/", "").strip()
            prop = await self.property_service.get_by_slug(slug)
            if prop:
                data = {
                    "name": prop.name,
                    "slug": prop.slug,
                    "description": prop.description,
                    "base_price": float(prop.base_price) if prop.base_price else 0,
                    "currency": prop.currency or "INR",
                }
                return ReadResourceResult(
                    contents=[
                        ResourceContent(
                            uri=uri,
                            mimeType="application/json",
                            text=json.dumps(data, indent=2),
                        )
                    ]
                )

        return ReadResourceResult(
            contents=[
                ResourceContent(
                    uri=uri,
                    mimeType="text/plain",
                    text=f"Resource not found: {uri}",
                )
            ]
        )

