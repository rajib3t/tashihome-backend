import asyncio
import uuid
from types import SimpleNamespace

from app.application.use_case.admin.properties.update_property_use_case import UpdatePropertyUseCase
from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_model import Property, PropertyStatus, PropertyType


class FakePropertyService:
    def __init__(self, property_):
        self.property = property_
        self.updated_properties = []

    async def get_by_public_id(self, public_id, flush=False, with_relations=None, **kwargs):
        return self.property if str(self.property.public_id) == str(public_id) else None

    async def get_by_vendor_and_name(self, vendor_id, name, flush=True):
        return None

    async def get_by_vendor_and_slug(self, vendor_id, slug, flush=True):
        return None

    async def update(self, property_, with_relations=None, commit=True):
        self.updated_properties.append(property_)
        return property_


class FakeLookupService:
    def __init__(self, entity=None):
        self.entity = entity

    async def get_by_public_id(self, public_id, flush=True, **kwargs):
        if self.entity is None:
            return None
        if str(self.entity.public_id) == str(public_id) or self.entity.id == int(public_id):
            return self.entity
        return None


class FakeAmenityService(FakeLookupService):
    pass


class FakeFacilityService(FakeLookupService):
    pass


class FakeRoomTypeService(FakeLookupService):
    pass


class FakePropertyAssociationService:
    def __init__(self):
        self.created = []
        self.deleted = []

    async def get_by_property_id(self, property_id, with_relations=None, flush=False):
        return []

    async def create(self, item, commit=True):
        self.created.append(item)
        return item

    async def delete(self, item, commit=True):
        self.deleted.append(item)


class FakeCurrentUser:
    def __init__(self, user_id=10):
        self.id = user_id


def test_update_property_updates_model_fields_and_syncs_associations():
    async def run_test():
        property_ = Property(
            vendor_id=1,
            location_id=1,
            city_id=1,
            room_type_id=1,
            name="Old Name",
            slug="old-name",
            description="old",
            price_per_night=100,
            currency="inr",
            sale_per_night=0,
            status=PropertyStatus.DRAFT,
            type=PropertyType.HOTEL,
        )
        property_.public_id = uuid.uuid4()

        property_service = FakePropertyService(property_)
        city_service = FakeLookupService(SimpleNamespace(id=2, public_id="city-1"))
        location_service = FakeLookupService(SimpleNamespace(id=3, public_id="location-1"))
        room_type_service = FakeLookupService(SimpleNamespace(id=4, public_id="room-type-1"))
        amenity_service = FakeAmenityService(SimpleNamespace(id=5, public_id="amenity-1"))
        facility_service = FakeFacilityService(SimpleNamespace(id=6, public_id="facility-1"))
        property_amenity_service = FakePropertyAssociationService()
        property_facility_service = FakePropertyAssociationService()
        property_food_option_service = FakePropertyAssociationService()
        current_user = FakeCurrentUser()

        use_case = UpdatePropertyUseCase(
            property_service=property_service,
            city_service=city_service,
            location_service=location_service,
            room_type_service=room_type_service,
            amenity_service=amenity_service,
            facility_service=facility_service,
            property_amenity_service=property_amenity_service,
            property_facility_service=property_facility_service,
            property_food_option_service=property_food_option_service,
            current_user=current_user,
        )

        data = SimpleNamespace(
            name="New Name",
            slug="new-name",
            description="new description",
            location_id="location-1",
            city_id="city-1",
            room_type_id="room-type-1",
            status="active",
            price_per_night=150,
            sale_per_night=120,
            currency="usd",
            is_featured=True,
            type=PropertyType.APARTMENT,
            amenity_ids=["amenity-1"],
            facility_ids=["facility-1"],
            food_option_ids=["breakfast"],
            price=None,
            sale_price=None,
            latitude=None,
            longitude=None,
        )

        updated_property = await use_case.execute(str(property_.public_id), data)

        assert updated_property.name == "New Name"
        assert updated_property.slug == "new-name"
        assert updated_property.description == "new description"
        assert updated_property.location_id == 3
        assert updated_property.city_id == 2
        assert updated_property.room_type_id == 4
        assert updated_property.status == PropertyStatus.ACTIVE
        assert updated_property.price_per_night == 150
        assert updated_property.sale_per_night == 120
        assert updated_property.currency == "USD"
        assert updated_property.is_featured is True
        assert updated_property.type == PropertyType.APARTMENT
        assert updated_property.updated_by == current_user.id
        assert any(isinstance(item, PropertyAmenity) for item in property_amenity_service.created)
        assert any(isinstance(item, PropertyFacility) for item in property_facility_service.created)

    asyncio.run(run_test())