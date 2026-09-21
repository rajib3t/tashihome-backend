import pytest
from types import SimpleNamespace
import uuid

from app.application.use_case.vendor.property.get_property_setup_steps_use_case import GetPropertySetupStepsUseCase
from app.models.property_model import Property, PropertyType
from app.services.property_steps_service import PropertyStepsService, STEPS


class FakePropertyService:
    def __init__(self, property_obj):
        self.property_obj = property_obj
        self.updated_steps = None

    async def get_by_public_id(self, public_id, with_relations=None, flush=False):
        if str(self.property_obj.public_id) == str(public_id):
            return self.property_obj
        return None

    async def update_steps(self, property_id, completed_steps, current_step=None, commit=True):
        self.updated_steps = completed_steps
        self.property_obj.completed_steps = completed_steps
        return self.property_obj


@pytest.mark.anyio
async def test_compute_steps_all_cases():
    steps_service = PropertyStepsService()

    # 1. Completely empty property -> 0 steps
    prop = SimpleNamespace(
        name=None,
        type=None,
        description=None,
        address=None,
        city_id=None,
        location_id=None,
        price_per_night=None,
        property_room_types=[],
        property_amenities=[],
        property_facilities=[],
        property_assets=[],
        cancellation_policy_id=None,
    )
    assert steps_service.compute_steps(prop) == []
    summary = steps_service.build_steps_summary([])
    assert summary["percent_complete"] == 0
    assert summary["is_complete"] is False

    # 2. Add basic info
    prop.name = "Cozy Cottage"
    prop.type = PropertyType.HOTEL
    prop.description = "A wonderful cottage"
    prop.address = "123 Mountain Rd"
    prop.city_id = 1
    prop.location_id = 2

    completed = steps_service.compute_steps(prop)
    assert completed == ["basic_info"]

    # 3. Add pricing
    prop.price_per_night = 150.0
    completed = steps_service.compute_steps(prop)
    assert "pricing" in completed

    # 4. Add room types, amenities, facilities, media, policies
    prop.property_room_types = [SimpleNamespace(id=1)]
    prop.property_amenities = [SimpleNamespace(id=1)]
    prop.property_facilities = [SimpleNamespace(id=1)]
    prop.property_assets = [SimpleNamespace(id=1)]
    prop.cancellation_policy_id = 10

    all_completed = steps_service.compute_steps(prop)
    assert set(all_completed) == set(STEPS)

    summary_all = steps_service.build_steps_summary(all_completed)
    assert summary_all["percent_complete"] == 100
    assert summary_all["is_complete"] is True
    assert all(summary_all["steps"].values())


@pytest.mark.anyio
async def test_get_property_setup_steps_use_case():
    pid = uuid.uuid4()
    prop = SimpleNamespace(
        id=42,
        public_id=pid,
        vendor_id=5,
        name="Villa Tashi",
        type=PropertyType.VILLA,
        description="Luxury villa",
        address="Cliffside 1",
        city_id=1,
        location_id=2,
        price_per_night=300.0,
        property_room_types=[SimpleNamespace(id=1)],
        property_amenities=[],
        property_facilities=[],
        property_assets=[],
        cancellation_policy_id=None,
        completed_steps=[],
    )

    property_service = FakePropertyService(prop)
    steps_service = PropertyStepsService()
    vendor_user = SimpleNamespace(id=5, role="vendor")

    use_case = GetPropertySetupStepsUseCase(
        property_service=property_service,
        steps_service=steps_service,
        current_user=vendor_user,
    )

    result = await use_case.execute(str(pid))
    assert result["steps"]["basic_info"] is True
    assert result["steps"]["pricing"] is True
    assert result["steps"]["room_types"] is True
    assert result["steps"]["amenities"] is False
    assert result["steps"]["facilities"] is False
    assert result["steps"]["media"] is False
    assert result["steps"]["policies"] is False
    assert result["percent_complete"] == round(3 / 7 * 100)
    assert result["is_complete"] is False

    # Check that update_steps was called to synchronize
    assert set(property_service.updated_steps) == {"basic_info", "pricing", "room_types"}

