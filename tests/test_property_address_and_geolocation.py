import asyncio
import uuid
import pytest
from types import SimpleNamespace

from app.application.dto.properties.property import (
    PropertyDTO,
    PropertyUpdateDTO,
    PropertyAddressDTO,
    PropertyGeolocationDTO,
    extract_property_address_and_geo,
)
from app.application.use_case.admin.properties.create_property_use_case import CreatePropertyUseCase
from app.application.use_case.admin.properties.update_property_use_case import UpdatePropertyUseCase
from app.application.use_case.admin.properties.property_serializer_mixin import PropertySerializerMixin
from app.application.use_case.vendor.property.create_property_use_case import VendorCreatePropertyUseCase
from app.application.use_case.vendor.property.update_property_use_case import VendorUpdatePropertyUseCase
from app.core.exceptions import AppException
from app.models.address_model import Address
from app.models.property_model import Property, PropertyStatus, PropertyType


class FakeAddressService:
    def __init__(self):
        self.addresses = {}

    async def get_property_address_by_owner_id(self, owner_id: int, flush=False):
        return self.addresses.get(owner_id)

    async def create(self, address: Address, commit=True):
        self.addresses[address.owner_id] = address
        return address

    async def update(self, address: Address, commit=True):
        self.addresses[address.owner_id] = address
        return address

    async def sync_property_address(
        self,
        property_id: int,
        address_line1: str,
        address_line2=None,
        postal_code="000000",
        country="India",
        commit=True,
    ):
        existing = self.addresses.get(property_id)
        if existing:
            existing.address_line1 = address_line1
            existing.address_line2 = address_line2
            existing.postal_code = postal_code
            existing.country = country
            return existing
        else:
            new_addr = Address(
                owner_type="property",
                owner_id=property_id,
                address_line1=address_line1,
                address_line2=address_line2,
                postal_code=postal_code,
                country=country,
            )
            new_addr.public_id = uuid.uuid4()
            self.addresses[property_id] = new_addr
            return new_addr


class FakePropertyService:
    def __init__(self, property_=None):
        self.property = property_
        self.created = []
        self.updated = []

    async def get_by_public_id(self, public_id, flush=False, with_relations=None, **kwargs):
        if self.property and str(self.property.public_id) == str(public_id):
            return self.property
        for p in self.created:
            if str(p.public_id) == str(public_id):
                return p
        return None

    async def get_by_vendor_and_name(self, vendor_id, name, flush=True):
        return None

    async def get_by_vendor_and_slug(self, vendor_id, slug, flush=True):
        return None

    async def create(self, property_, with_relations=None, commit=True):
        property_.id = 1
        if not getattr(property_, "public_id", None):
            property_.public_id = uuid.uuid4()
        self.created.append(property_)
        self.property = property_
        return property_

    async def update(self, property_, with_relations=None, commit=True):
        self.updated.append(property_)
        self.property = property_
        return property_

    async def update_steps(self, property_id, completed_steps, commit=True):
        if self.property and self.property.id == property_id:
            self.property.completed_steps = completed_steps


class FakeLookupService:
    def __init__(self, entity=None):
        self.entity = entity

    async def get_by_public_id(self, public_id, flush=True, **kwargs):
        if self.entity is None:
            return None
        if str(self.entity.public_id) == str(public_id) or self.entity.id == int(public_id):
            return self.entity
        return None

    async def get_user_by_public_id(self, public_id, flush=True, **kwargs):
        return await self.get_by_public_id(public_id, flush=flush, **kwargs)


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


def test_vendor_create_property_with_manual_address():
    async def run_test():
        prop_svc = FakePropertyService()
        addr_svc = FakeAddressService()
        city = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="Gangtok", slug="gangtok")
        location = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="MG Marg", slug="mg-marg")
        current_user = FakeCurrentUser(user_id=10)

        use_case = VendorCreatePropertyUseCase(
            property_service=prop_svc,
            city_service=FakeLookupService(city),
            location_service=FakeLookupService(location),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        dto = PropertyDTO(
            name="Host Himalayan Home",
            city_id=str(city.public_id),
            location_id=str(location.public_id),
            type="home_stay",
            description="Cozy homestay in the hills",
            price_per_night=1500,
            address_line1="Tibet Road, Near Star Cinema",
            address_line2="Floor 2",
            postal_code="737101",
            country="India",
        )

        res = await use_case.execute(dto)

        # Verified that property was created
        assert res is not None
        assert res["name"] == "Host Himalayan Home"
        assert res["address"] == "Tibet Road, Near Star Cinema, Floor 2, 737101, India"
        assert res["latitude"] is None
        assert res["longitude"] is None
        assert res["geolocation"] is None

        # Verify address_details and manual_address in response
        assert res["address_details"] is not None
        assert res["address_details"]["address_line1"] == "Tibet Road, Near Star Cinema"
        assert res["address_details"]["address_line2"] == "Floor 2"
        assert res["address_details"]["postal_code"] == "737101"
        assert res["address_details"]["country"] == "India"
        assert res["manual_address"] == res["address_details"]

        # Verify Address record synced in AddressService
        addr_in_db = addr_svc.addresses.get(1)
        assert addr_in_db is not None
        assert addr_in_db.owner_type == "property"
        assert addr_in_db.owner_id == 1
        assert addr_in_db.address_line1 == "Tibet Road, Near Star Cinema"

    asyncio.run(run_test())


def test_vendor_create_property_with_geolocation_raises_403():
    async def run_test():
        prop_svc = FakePropertyService()
        addr_svc = FakeAddressService()
        city = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="Gangtok", slug="gangtok")
        location = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="MG Marg", slug="mg-marg")
        current_user = FakeCurrentUser(user_id=10)

        use_case = VendorCreatePropertyUseCase(
            property_service=prop_svc,
            city_service=FakeLookupService(city),
            location_service=FakeLookupService(location),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        # Host attempts to pass latitude and longitude
        dto = PropertyDTO(
            name="Host Homestay With Coordinates",
            city_id=str(city.public_id),
            location_id=str(location.public_id),
            type="home_stay",
            description="Cozy homestay",
            address="Upper Pelling",
            latitude=27.325,
            longitude=88.612,
        )

        with pytest.raises(AppException) as exc_info:
            await use_case.execute(dto)

        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "GEOLOCATION_ADMIN_ONLY"

    asyncio.run(run_test())


def test_vendor_update_property_with_geolocation_raises_403():
    async def run_test():
        existing_prop = Property(
            vendor_id=10,
            location_id=1,
            city_id=1,
            name="Host Homestay",
            slug="host-homestay",
            address="Old Address",
            latitude=27.1,
            longitude=88.2,
            price_per_night=1000,
            status=PropertyStatus.DRAFT,
            type=PropertyType.HOME_STAY,
        )
        existing_prop.id = 1
        existing_prop.public_id = uuid.uuid4()

        prop_svc = FakePropertyService(existing_prop)
        addr_svc = FakeAddressService()
        current_user = FakeCurrentUser(user_id=10)

        use_case = VendorUpdatePropertyUseCase(
            property_service=prop_svc,
            city_service=FakeLookupService(None),
            location_service=FakeLookupService(None),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        update_dto = PropertyUpdateDTO(
            latitude=27.33,
            longitude=88.66,
        )

        with pytest.raises(AppException) as exc_info:
            await use_case.execute(str(existing_prop.public_id), update_dto)

        assert exc_info.value.status_code == 403
        assert exc_info.value.error_code == "GEOLOCATION_ADMIN_ONLY"

    asyncio.run(run_test())


def test_vendor_update_property_manual_address():
    async def run_test():
        existing_prop = Property(
            vendor_id=10,
            location_id=1,
            city_id=1,
            name="Host Homestay",
            slug="host-homestay",
            address="Old Address",
            price_per_night=1000,
            status=PropertyStatus.DRAFT,
            type=PropertyType.HOME_STAY,
        )
        existing_prop.id = 1
        existing_prop.public_id = uuid.uuid4()

        prop_svc = FakePropertyService(existing_prop)
        addr_svc = FakeAddressService()
        current_user = FakeCurrentUser(user_id=10)

        use_case = VendorUpdatePropertyUseCase(
            property_service=prop_svc,
            city_service=FakeLookupService(None),
            location_service=FakeLookupService(None),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        update_dto = PropertyUpdateDTO(
            address_line1="New Pelling Main Road",
            address_line2="Behind Dzong",
            postal_code="737113",
            country="India",
        )

        res = await use_case.execute(str(existing_prop.public_id), update_dto)

        assert res["address"] == "New Pelling Main Road, Behind Dzong, 737113, India"
        assert res["address_details"]["address_line1"] == "New Pelling Main Road"
        assert res["address_details"]["postal_code"] == "737113"

        addr_in_db = addr_svc.addresses.get(1)
        assert addr_in_db is not None
        assert addr_in_db.address_line1 == "New Pelling Main Road"

    asyncio.run(run_test())


def test_admin_create_property_with_manual_and_geo_address():
    async def run_test():
        prop_svc = FakePropertyService()
        addr_svc = FakeAddressService()
        city = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="Gangtok", slug="gangtok")
        location = SimpleNamespace(id=1, public_id=uuid.uuid4(), name="MG Marg", slug="mg-marg")
        vendor = SimpleNamespace(id=2, public_id=uuid.uuid4())
        current_user = FakeCurrentUser(user_id=1)

        use_case = CreatePropertyUseCase(
            property_service=prop_svc,
            user_service=FakeLookupService(vendor),
            city_service=FakeLookupService(city),
            location_service=FakeLookupService(location),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        dto = PropertyDTO(
            name="Admin Created Luxury Homestay",
            vendor_id=str(vendor.public_id),
            city_id=str(city.public_id),
            location_id=str(location.public_id),
            type="villa",
            description="Luxury stay",
            price_per_night=5000,
            address_line1="45 Ridge Road",
            address_line2="Near Palace",
            postal_code="737103",
            country="India",
            latitude=27.3389,
            longitude=88.6178,
        )

        res = await use_case.execute(dto)

        # Admin successfully added BOTH manual address AND geo address
        assert res["name"] == "Admin Created Luxury Homestay"
        assert res["address"] == "45 Ridge Road, Near Palace, 737103, India"
        assert res["latitude"] == 27.3389
        assert res["longitude"] == 88.6178
        assert res["geolocation"] == {"latitude": 27.3389, "longitude": 88.6178}
        assert res["address_details"]["address_line1"] == "45 Ridge Road"
        assert res["address_details"]["postal_code"] == "737103"

        addr_in_db = addr_svc.addresses.get(1)
        assert addr_in_db is not None
        assert addr_in_db.address_line1 == "45 Ridge Road"
        assert addr_in_db.owner_type == "property"

    asyncio.run(run_test())


def test_admin_update_property_with_manual_and_geo_address():
    async def run_test():
        existing_prop = Property(
            vendor_id=2,
            location_id=1,
            city_id=1,
            name="Resort",
            slug="resort",
            address="Old Address",
            latitude=27.0,
            longitude=88.0,
            price_per_night=3000,
            status=PropertyStatus.ACTIVE,
            type=PropertyType.RESORT,
        )
        existing_prop.id = 1
        existing_prop.public_id = uuid.uuid4()

        prop_svc = FakePropertyService(existing_prop)
        addr_svc = FakeAddressService()
        current_user = FakeCurrentUser(user_id=1)

        use_case = UpdatePropertyUseCase(
            property_service=prop_svc,
            city_service=FakeLookupService(None),
            location_service=FakeLookupService(None),
            room_type_service=FakeLookupService(None),
            amenity_service=FakeLookupService(None),
            facility_service=FakeLookupService(None),
            property_amenity_service=FakePropertyAssociationService(),
            property_facility_service=FakePropertyAssociationService(),
            property_food_option_service=FakePropertyAssociationService(),
            property_room_type_service=FakePropertyAssociationService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
            address_service=addr_svc,
        )

        update_dto = PropertyUpdateDTO(
            address_line1="Updated Hilltop Lane",
            postal_code="737102",
            latitude=27.3456,
            longitude=88.6234,
        )

        res = await use_case.execute(str(existing_prop.public_id), update_dto)

        assert res["address"] == "Updated Hilltop Lane, 737102, India"
        assert res["latitude"] == 27.3456
        assert res["longitude"] == 88.6234
        assert res["geolocation"] == {"latitude": 27.3456, "longitude": 88.6234}
        assert res["address_details"]["address_line1"] == "Updated Hilltop Lane"

    asyncio.run(run_test())


def test_latitude_longitude_validation_out_of_range():
    # Latitude > 90
    with pytest.raises(AppException) as exc_lat:
        PropertyDTO(name="Invalid Lat", latitude=95.0, longitude=88.0)
    assert exc_lat.value.error_code == "LATITUDE_OUT_OF_RANGE"

    # Longitude > 180
    with pytest.raises(AppException) as exc_lon:
        PropertyDTO(name="Invalid Lon", latitude=27.0, longitude=190.0)
    assert exc_lon.value.error_code == "LONGITUDE_OUT_OF_RANGE"


def test_property_serializer_mixin_outputs_address_details_and_geolocation():
    async def run_test():
        class TestSerializer(PropertySerializerMixin):
            def __init__(self):
                self.storage_service = FakeStorageService()

        serializer = TestSerializer()

        prop = Property(
            vendor_id=1,
            location_id=1,
            city_id=1,
            name="Test Serializer Homestay",
            slug="test-serializer-homestay",
            address="Kazi Road, Gangtok",
            latitude=27.33,
            longitude=88.61,
            price_per_night=2000,
            status=PropertyStatus.ACTIVE,
            type=PropertyType.HOME_STAY,
        )
        prop.id = 1
        prop.public_id = uuid.uuid4()

        # Without addresses relation loaded
        res = await serializer.serialize_property(prop)
        assert res["address"] == "Kazi Road, Gangtok"
        assert res["address_details"] == {
            "id": None,
            "address_line1": "Kazi Road, Gangtok",
            "address_line2": None,
            "postal_code": None,
            "country": "India",
        }
        assert res["geolocation"] == {"latitude": 27.33, "longitude": 88.61}

        # With addresses relation loaded
        addr = Address(
            owner_type="property",
            owner_id=1,
            address_line1="Kazi Road",
            address_line2="Opp. Secretariat",
            postal_code="737101",
            country="India",
        )
        addr.public_id = uuid.uuid4()
        prop.addresses = [addr]

        res_loaded = await serializer.serialize_property(prop)
        assert res_loaded["address_details"] == {
            "id": str(addr.public_id),
            "address_line1": "Kazi Road",
            "address_line2": "Opp. Secretariat",
            "postal_code": "737101",
            "country": "India",
        }

    asyncio.run(run_test())


def test_get_property_use_case_without_loaded_addresses():
    from app.application.use_case.admin.properties.get_property_use_case import GetPropertyUseCase

    async def run_test():
        prop = Property(
            vendor_id=1,
            location_id=1,
            city_id=1,
            name="Get Property Homestay",
            slug="get-property-homestay",
            address="Tibet Road, Gangtok",
            latitude=27.33,
            longitude=88.61,
            price_per_night=2500,
            status=PropertyStatus.ACTIVE,
            type=PropertyType.HOME_STAY,
        )
        prop.id = 10
        prop.public_id = uuid.uuid4()

        class FakePropertyService:
            async def get_by_public_id(self, public_id, with_relations=None, flush=False):
                assert with_relations is not None
                assert with_relations.get("addresses") is True
                return prop

        class FakeStorageService:
            async def generate_presigned_url(self, path):
                return f"https://s3/{path}"

        current_user = SimpleNamespace(id=1, role=SimpleNamespace(value="admin"))
        use_case = GetPropertyUseCase(
            property_service=FakePropertyService(),
            storage_service=FakeStorageService(),
            current_user=current_user,
        )

        result = await use_case.execute(str(prop.public_id))
        assert result is not None
        assert result["name"] == "Get Property Homestay"
        assert result["address"] == "Tibet Road, Gangtok"
        assert result["address_details"]["address_line1"] == "Tibet Road, Gangtok"
        assert result["geolocation"] == {"latitude": 27.33, "longitude": 88.61}

    asyncio.run(run_test())

