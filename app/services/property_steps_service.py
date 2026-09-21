from __future__ import annotations
from typing import Any, Dict, List, Optional


STEPS = [
    "basic_info",
    "pricing",
    "room_types",
    "amenities",
    "facilities",
    "media",
    "policies",
]


class PropertyStepsService:
    @staticmethod
    def compute_steps(property_obj: Any) -> list[str]:
        """
        Computes the completed steps for a given Property instance.
        Requires that relevant relationships (property_room_types, property_amenities,
        property_facilities, property_assets) are loaded if checking them.
        """
        completed = []

        # 1. basic_info: name, type, description, address, city_id, location_id
        if all([
            property_obj.name,
            property_obj.type,
            property_obj.description,
            property_obj.address,
            property_obj.city_id,
            property_obj.location_id,
        ]):
            completed.append("basic_info")

        # 2. pricing: price_per_night > 0
        if property_obj.price_per_night and property_obj.price_per_night > 0:
            completed.append("pricing")

        # 3. room_types: at least one room type assigned
        if hasattr(property_obj, "property_room_types") and property_obj.property_room_types:
            completed.append("room_types")

        # 4. amenities: at least one amenity assigned
        if hasattr(property_obj, "property_amenities") and property_obj.property_amenities:
            completed.append("amenities")

        # 5. facilities: at least one facility assigned
        if hasattr(property_obj, "property_facilities") and property_obj.property_facilities:
            completed.append("facilities")

        # 6. media: at least one image uploaded
        if hasattr(property_obj, "property_assets") and property_obj.property_assets:
            completed.append("media")

        # 7. policies: cancellation policy assigned
        if getattr(property_obj, "cancellation_policy_id", None):
            completed.append("policies")

        return completed

    @staticmethod
    def build_steps_summary(completed_steps: list[str]) -> Dict[str, Any]:
        total = len(STEPS)
        valid_completed = [s for s in STEPS if s in completed_steps]
        count = len(valid_completed)
        percent = round(count / total * 100) if total > 0 else 0
        return {
            "steps": {s: s in valid_completed for s in STEPS},
            "completed_steps": valid_completed,
            "percent_complete": percent,
            "is_complete": count == total,
        }

