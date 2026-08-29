import asyncio
import uuid
from types import SimpleNamespace

from app.application.use_case.admin.properties.update_property_use_case import UpdatePropertyUseCase
from app.models.property_amenity_model import PropertyAmenity
from app.models.property_facility_model import PropertyFacility
from app.models.property_room_type_model import PropertyRoomType
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


class FakeStorageService:
    async def generate_presigned_url(self, path):
        return path


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
        property_.id = 1
        property_.vendor = SimpleNamespace(public_id=uuid.uuid4(), full_name="Vendor", email="v@example.com", is_profile_image_url=None)
        property_.location = SimpleNamespace(public_id=uuid.uuid4(), name="Location")
        property_.city = SimpleNamespace(public_id=uuid.uuid4(), name="City")
        property_.property_room_types = []
        property_.property_amenities = []
        property_.property_facilities = []
        property_.property_food_options = []
        property_.property_assets = []

        property_service = FakePropertyService(property_)
        city_service = FakeLookupService(SimpleNamespace(id=2, public_id="city-1"))
        location_service = FakeLookupService(SimpleNamespace(id=3, public_id="location-1"))
        room_type_service = FakeLookupService(SimpleNamespace(id=4, public_id="room-type-1"))
        amenity_service = FakeAmenityService(SimpleNamespace(id=5, public_id="amenity-1"))
        facility_service = FakeFacilityService(SimpleNamespace(id=6, public_id="facility-1"))
        property_amenity_service = FakePropertyAssociationService()
        property_facility_service = FakePropertyAssociationService()
        property_food_option_service = FakePropertyAssociationService()
        property_room_type_service = FakePropertyAssociationService()
        storage_service = FakeStorageService()
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
            property_room_type_service=property_room_type_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        data = SimpleNamespace(
            name="New Name",
            slug="new-name",
            description="new description",
            location_id="location-1",
            city_id="city-1",
            room_type_id="room-type-1",
            room_type_ids=None,
            room_types=None,
            status="active",
            price_per_night=150,
            sale_per_night=120,
            currency="usd",
            is_featured=True,
            type=PropertyType.APARTMENT,
            amenities=None,
            amenity_ids=["amenity-1"],
            facility=None,
            facilities=None,
            facility_ids=["facility-1"],
            food_options=None,
            food_option_ids=["breakfast"],
            price=None,
            sale_price=None,
            latitude=None,
            longitude=None,
            address=None,
        )

        updated_dict = await use_case.execute(str(property_.public_id), data)

        assert updated_dict["name"] == "New Name"
        assert updated_dict["slug"] == "new-name"
        assert updated_dict["description"] == "new description"
        assert property_.location_id == 3
        assert property_.city_id == 2
        assert updated_dict["status"] == "active"
        assert updated_dict["price_per_night"] == 150
        assert updated_dict["sale_per_night"] == 120
        assert updated_dict["currency"] == "USD"
        assert updated_dict["is_featured"] is True
        assert property_.updated_by == current_user.id
        assert any(isinstance(item, PropertyAmenity) for item in property_amenity_service.created)
        assert any(isinstance(item, PropertyRoomType) for item in property_room_type_service.created)

    asyncio.run(run_test())


def test_create_property_with_room_types():
    from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
    from app.application.dto.properties.property import PropertyDTO, PropertyRoomTypeDTO

    async def run_test():
        class FakeCreatePropertyService(FakePropertyService):
            async def create(self, property_, commit=True):
                property_.id = 1
                property_.public_id = uuid.uuid4()
                property_.vendor = SimpleNamespace(public_id=uuid.uuid4(), full_name="Vendor", email="v@example.com", is_profile_image_url=None)
                property_.location = SimpleNamespace(public_id=uuid.uuid4(), name="Location")
                property_.city = SimpleNamespace(public_id=uuid.uuid4(), name="City")
                property_.property_room_types = []
                property_.property_amenities = []
                property_.property_facilities = []
                property_.property_food_options = []
                property_.property_assets = []
                return property_

        property_service = FakeCreatePropertyService(None)
        user_service = FakeLookupService(SimpleNamespace(id=1, public_id="vendor-1"))
        city_service = FakeLookupService(SimpleNamespace(id=2, public_id="city-1"))
        location_service = FakeLookupService(SimpleNamespace(id=3, public_id="location-1"))
        room_type_service = FakeLookupService(SimpleNamespace(id=4, public_id="room-type-1"))
        amenity_service = FakeAmenityService(SimpleNamespace(id=5, public_id="amenity-1"))
        facility_service = FakeFacilityService(SimpleNamespace(id=6, public_id="facility-1"))
        property_amenity_service = FakePropertyAssociationService()
        property_facility_service = FakePropertyAssociationService()
        property_food_option_service = FakePropertyAssociationService()
        property_room_type_service = FakePropertyAssociationService()
        storage_service = FakeStorageService()
        current_user = FakeCurrentUser()

        use_case = CreatePropertyUseCase(
            property_service=property_service,
            user_service=user_service,
            city_service=city_service,
            location_service=location_service,
            room_type_service=room_type_service,
            amenity_service=amenity_service,
            facility_service=facility_service,
            property_amenity_service=property_amenity_service,
            property_facility_service=property_facility_service,
            property_food_option_service=property_food_option_service,
            property_room_type_service=property_room_type_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        dto = PropertyDTO(
            name="New Hotel",
            vendor_id="vendor-1",
            city_id="city-1",
            location_id="location-1",
            room_types=[PropertyRoomTypeDTO(id="room-type-1", total_units=3)],
            price_per_night=100.0,
        )

        result = await use_case.execute(dto)

        assert result["name"] == "New Hotel"
        assert len(property_room_type_service.created) == 1
        created_rt = property_room_type_service.created[0]
        assert isinstance(created_rt, PropertyRoomType)
        assert created_rt.room_type_id == 4
        assert created_rt.total_units == 3

    asyncio.run(run_test())