from typing import Any, Dict, Optional
from app.application.use_case.base_use_case import BaseUseCase
from app.core.exceptions import AppException
from app.deps.auth import CurrentUser
from app.services.property_service import PropertyService
from app.services.property_steps_service import PropertyStepsService


class GetPropertySetupStepsUseCase(BaseUseCase):
    def __init__(
        self,
        property_service: PropertyService,
        steps_service: PropertyStepsService,
        current_user: CurrentUser,
    ):
        self.property_service = property_service
        self.steps_service = steps_service
        self.current_user = current_user

    async def execute(self, property_id: str) -> Dict[str, Any]:
        property_data = await self.property_service.get_by_public_id(
            property_id,
            with_relations={
                "city": True,
                "location": True,
                "vendor": True,
                "property_room_types": True,
                "property_amenities": True,
                "property_facilities": True,
                "property_food_options": True,
                "property_assets": True,
            },
        )

        if not property_data:
            raise AppException(
                message="Property not found.",
                error_code="PROPERTY_NOT_FOUND",
                status_code=404,
            )

        # If user is a vendor, ensure ownership
        user_role = getattr(self.current_user, "role", None)
        role_str = user_role.value if hasattr(user_role, "value") else str(user_role or "")
        if role_str.lower() == "vendor" and property_data.vendor_id != self.current_user.id:
            raise AppException(
                status_code=403,
                message="You are not authorized to access this property.",
                field="property_id",
                error_code="PROPERTY_ACCESS_DENIED",
            )

        completed = self.steps_service.compute_steps(property_data)

        # Update persisted completed_steps if changed
        if set(completed) != set(property_data.completed_steps or []):
            await self.property_service.update_steps(
                property_id=property_data.id,
                completed_steps=completed,
                commit=True,
            )

        return self.steps_service.build_steps_summary(completed)

