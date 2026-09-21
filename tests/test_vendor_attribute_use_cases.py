import pytest
from types import SimpleNamespace
import uuid

from app.application.dto.attributes.amenity import AmenityDTO, AmenityQueryDTO
from app.application.dto.attributes.facility import FacilityDTO
from app.application.dto.attributes.room_type import RoomTypeDTO
from app.application.use_case.vendor.attributes.amenity.create_vendor_amenity_use_case import VendorCreateAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.delete_vendor_amenity_use_case import VendorDeleteAmenityUseCase
from app.application.use_case.vendor.attributes.amenity.list_vendor_amenities_use_case import VendorListAmenitiesUseCase
from app.application.use_case.vendor.attributes.amenity.update_vendor_amenity_use_case import VendorUpdateAmenityUseCase
from app.application.use_case.vendor.attributes.facility.create_vendor_facility_use_case import VendorCreateFacilityUseCase
from app.application.use_case.vendor.attributes.room_type.create_vendor_room_type_use_case import VendorCreateRoomTypeUseCase
from app.core.exceptions import AppException
from app.models.amenity_model import Amenity, AmenityStatus
from app.models.facility_model import Facility
from app.models.room_type_model import RoomType
from app.repositories.base_repository import Page


class InMemoryAttributeService:
    def __init__(self, model_cls):
        self.model_cls = model_cls
        self.items: list = []
        self._next_id = 1

    async def create(self, item, commit=True):
        item.id = self._next_id
        self._next_id += 1
        if not getattr(item, "public_id", None):
            item.public_id = uuid.uuid4()
        self.items.append(item)
        return item

    async def update(self, item, commit=True):
        for idx, existing in enumerate(self.items):
            if existing.id == item.id:
                self.items[idx] = item
                return item
        return item

    async def delete(self, item, commit=True):
        self.items = [i for i in self.items if i.id != item.id]

    async def get_by_public_id(self, public_id, flush=False):
        for item in self.items:
            if str(item.public_id) == str(public_id):
                return item
        return None

    async def get_by_name(self, name, flush=False):
        for item in self.items:
            if item.name.lower() == name.lower():
                return item
        return None

    async def get_by_name_and_vendor(self, name, vendor_id=None, flush=False):
        for item in self.items:
            if item.name.lower() == name.lower() and getattr(item, "vendor_id", None) == vendor_id:
                return item
        return None

    async def list(self, page=1, page_size=20, search=None, filters=None, vendor_id=None, scope="all", flush=False):
        matched = list(self.items)
        if search:
            matched = [i for i in matched if search.lower() in i.name.lower()]
        if scope == "global":
            matched = [i for i in matched if getattr(i, "vendor_id", None) is None]
        elif scope == "vendor":
            matched = [i for i in matched if getattr(i, "vendor_id", None) == vendor_id]
        elif scope == "vendor_combined":
            matched = [i for i in matched if getattr(i, "vendor_id", None) is None or getattr(i, "vendor_id", None) == vendor_id]
        return Page(items=matched, total=len(matched), page=page, page_size=page_size)


class DummyStorageService:
    async def get_display_url(self, path):
        return f"https://cdn.example.com/{path}"

    async def delete_object(self, path):
        pass


@pytest.mark.anyio
async def test_vendor_create_amenity_success():
    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    vendor_user = SimpleNamespace(id=10, role="vendor")

    # Global amenity exists
    global_amenity = Amenity(id=1, public_id=uuid.uuid4(), name="WiFi", vendor_id=None)
    await service.create(global_amenity)

    use_case = VendorCreateAmenityUseCase(service, storage, verify_csrf=True, current_user=vendor_user)
    created = await use_case.execute(AmenityDTO(name="Private Balcony", icon=None))

    assert created.name == "Private Balcony"
    assert created.vendor_id == 10
    assert created.is_global is False


@pytest.mark.anyio
async def test_vendor_cannot_create_global_duplicate():
    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    vendor_user = SimpleNamespace(id=10, role="vendor")

    # Global amenity "Swimming Pool"
    await service.create(Amenity(id=1, public_id=uuid.uuid4(), name="Swimming Pool", vendor_id=None))

    use_case = VendorCreateAmenityUseCase(service, storage, verify_csrf=True, current_user=vendor_user)
    with pytest.raises(AppException) as exc:
        await use_case.execute(AmenityDTO(name="Swimming Pool", icon=None))
    assert exc.value.status_code == 409
    assert exc.value.error_code == "AMENITY_ALREADY_EXISTS_GLOBAL"


@pytest.mark.anyio
async def test_two_vendors_can_create_same_attribute_name():
    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    vendor_1 = SimpleNamespace(id=10, role="vendor")
    vendor_2 = SimpleNamespace(id=20, role="vendor")

    uc_1 = VendorCreateAmenityUseCase(service, storage, verify_csrf=True, current_user=vendor_1)
    uc_2 = VendorCreateAmenityUseCase(service, storage, verify_csrf=True, current_user=vendor_2)

    a1 = await uc_1.execute(AmenityDTO(name="Mountain View", icon=None))
    a2 = await uc_2.execute(AmenityDTO(name="Mountain View", icon=None))

    assert a1.name == "Mountain View"
    assert a1.vendor_id == 10
    assert a2.name == "Mountain View"
    assert a2.vendor_id == 20

    # Same vendor creating duplicate again should fail
    with pytest.raises(AppException) as exc:
        await uc_1.execute(AmenityDTO(name="Mountain View", icon=None))
    assert exc.value.status_code == 409
    assert exc.value.error_code == "AMENITY_ALREADY_EXISTS_VENDOR"


@pytest.mark.anyio
async def test_vendor_cannot_modify_or_delete_global_or_other_vendor_amenity():
    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    vendor_1 = SimpleNamespace(id=10, role="vendor")
    vendor_2 = SimpleNamespace(id=20, role="vendor")

    global_amenity = Amenity(id=1, public_id=uuid.uuid4(), name="Global Gym", vendor_id=None)
    await service.create(global_amenity)

    vendor2_amenity = Amenity(id=2, public_id=uuid.uuid4(), name="Vendor2 Sauna", vendor_id=20)
    await service.create(vendor2_amenity)

    update_uc = VendorUpdateAmenityUseCase(service, storage, current_user=vendor_1)
    delete_uc = VendorDeleteAmenityUseCase(service, storage, current_user=vendor_1)

    # Attempt to edit global -> 403
    with pytest.raises(AppException) as exc:
        await update_uc.execute(str(global_amenity.public_id), AmenityDTO(name="Renamed Gym", icon=None))
    assert exc.value.status_code == 403

    # Attempt to delete global -> 403
    with pytest.raises(AppException) as exc:
        await delete_uc.execute(str(global_amenity.public_id))
    assert exc.value.status_code == 403

    # Attempt to edit vendor 2 amenity -> 403
    with pytest.raises(AppException) as exc:
        await update_uc.execute(str(vendor2_amenity.public_id), AmenityDTO(name="Hacked Sauna", icon=None))
    assert exc.value.status_code == 403


@pytest.mark.anyio
async def test_vendor_list_combined_amenities():
    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    vendor_1 = SimpleNamespace(id=10, role="vendor")

    await service.create(Amenity(id=1, public_id=uuid.uuid4(), name="Global WiFi", vendor_id=None))
    await service.create(Amenity(id=2, public_id=uuid.uuid4(), name="Vendor 1 Garden", vendor_id=10))
    await service.create(Amenity(id=3, public_id=uuid.uuid4(), name="Vendor 2 Terrace", vendor_id=20))

    list_uc = VendorListAmenitiesUseCase(service, storage, current_user=vendor_1)
    result = await list_uc.execute(AmenityQueryDTO(page=1, size=20))

    names = [item.name for item in result.items]
    assert "Global WiFi" in names
    assert "Vendor 1 Garden" in names
    assert "Vendor 2 Terrace" not in names


@pytest.mark.anyio
async def test_vendor_create_room_type():
    service = InMemoryAttributeService(RoomType)
    vendor_1 = SimpleNamespace(id=10, role="vendor")

    await service.create(RoomType(id=1, public_id=uuid.uuid4(), name="Standard Room", capacity=2, vendor_id=None))

    uc = VendorCreateRoomTypeUseCase(service, verify_csrf=True, current_user=vendor_1)
    rt = await uc.execute(RoomTypeDTO(name="Deluxe Penthouse", capacity=4))

    assert rt.name == "Deluxe Penthouse"
    assert rt.capacity == 4
    assert rt.vendor_id == 10
    assert rt.is_global is False


@pytest.mark.anyio
async def test_admin_create_and_update_vendor_scoped_amenity():
    from app.application.use_case.admin.attributes.attribute.create_amenity_use_case import CreateAmenityUseCase
    from app.application.use_case.admin.attributes.attribute.update_amenity_use_case import UpdateAmenityUseCase

    service = InMemoryAttributeService(Amenity)
    storage = DummyStorageService()
    admin_user = SimpleNamespace(id=1, role="admin")
    vendor_uuid = uuid.uuid4()
    mock_vendor = SimpleNamespace(id=55, public_id=vendor_uuid)

    class MockUserService:
        async def get_user_by_public_id(self, pid, flush=False):
            if str(pid) == str(vendor_uuid):
                return mock_vendor
            return None

        async def get_user_by_id(self, uid, flush=False):
            if uid == 55:
                return mock_vendor
            return None

    user_service = MockUserService()
    create_uc = CreateAmenityUseCase(service, storage, verify_csrf=False, current_user=admin_user, user_service=user_service)
    amenity = await create_uc.execute(AmenityDTO(name="Vendor Specific Spa", icon=None, vendor_id=str(vendor_uuid)))

    assert amenity.name == "Vendor Specific Spa"
    assert amenity.vendor_id == 55
    assert amenity.vendor_public_id == str(vendor_uuid)

    update_uc = UpdateAmenityUseCase(service, storage, current_user=admin_user, user_service=user_service)
    updated = await update_uc.execute(str(amenity.public_id), AmenityDTO(name="Vendor Specific Spa & Wellness", icon=None, vendor_id=str(vendor_uuid)))

    assert updated.name == "Vendor Specific Spa & Wellness"
    assert updated.vendor_id == 55
    assert updated.vendor_public_id == str(vendor_uuid)


@pytest.mark.anyio
async def test_admin_create_and_update_vendor_scoped_room_type():
    from app.application.use_case.admin.attributes.attribute.create_room_type_use_case import CreateRoomTypeUseCase
    from app.application.use_case.admin.attributes.attribute.update_room_type_use_case import UpdateRoomTypeUseCase

    service = InMemoryAttributeService(RoomType)
    admin_user = SimpleNamespace(id=1, role="admin")
    vendor_uuid = uuid.uuid4()
    mock_vendor = SimpleNamespace(id=77, public_id=vendor_uuid)

    class MockUserService:
        async def get_user_by_public_id(self, pid, flush=False):
            if str(pid) == str(vendor_uuid):
                return mock_vendor
            return None

        async def get_user_by_id(self, uid, flush=False):
            if uid == 77:
                return mock_vendor
            return None

    user_service = MockUserService()
    create_uc = CreateRoomTypeUseCase(service, verify_csrf=False, current_user=admin_user, user_service=user_service)
    rt = await create_uc.execute(RoomTypeDTO(name="Vendor Villa", capacity=6, vendor_id=str(vendor_uuid)))

    assert rt.name == "Vendor Villa"
    assert rt.capacity == 6
    assert rt.vendor_id == 77
    assert rt.vendor_public_id == str(vendor_uuid)

    update_uc = UpdateRoomTypeUseCase(service, current_user=admin_user, user_service=user_service)
    updated_rt = await update_uc.execute(str(rt.public_id), RoomTypeDTO(name="Vendor Luxury Villa", capacity=8, vendor_id=str(vendor_uuid)))

    assert updated_rt.name == "Vendor Luxury Villa"
    assert updated_rt.capacity == 8
    assert updated_rt.vendor_id == 77
    assert updated_rt.vendor_public_id == str(vendor_uuid)


@pytest.mark.anyio
async def test_admin_list_amenities_scope_and_vendor():
    from app.application.use_case.admin.attributes.attribute.get_amenity_use_case import ListAmenitiesUseCase

    service = InMemoryAttributeService(Amenity)
    admin_user = SimpleNamespace(id=1, role="admin")
    vendor_1_uuid = uuid.uuid4()
    vendor_2_uuid = uuid.uuid4()
    v1 = SimpleNamespace(id=10, public_id=vendor_1_uuid)
    v2 = SimpleNamespace(id=20, public_id=vendor_2_uuid)

    class MockUserService:
        async def get_user_by_public_id(self, pid, flush=False):
            if str(pid) == str(vendor_1_uuid):
                return v1
            if str(pid) == str(vendor_2_uuid):
                return v2
            return None

        async def get_user_by_id(self, uid, flush=False):
            if uid == 10:
                return v1
            if uid == 20:
                return v2
            return None

    user_service = MockUserService()
    storage = SimpleNamespace()

    # Create 1 global, 1 vendor_1, 1 vendor_2 amenity
    await service.create(Amenity(name="Global WiFi", vendor_id=None, status=AmenityStatus.ACTIVE))
    await service.create(Amenity(name="V1 Fireplace", vendor_id=10, status=AmenityStatus.ACTIVE))
    await service.create(Amenity(name="V2 Hot Tub", vendor_id=20, status=AmenityStatus.ACTIVE))

    list_uc = ListAmenitiesUseCase(service, storage, current_user=admin_user, user_service=user_service)

    # 1. Global only
    res_global = await list_uc.execute(AmenityQueryDTO(scope="global"))
    assert len(res_global.items) == 1
    assert res_global.items[0].name == "Global WiFi"

    # 2. Vendor 1 combined (global + vendor 1)
    res_v1_combined = await list_uc.execute(AmenityQueryDTO(scope="vendor_combined", vendor_id=str(vendor_1_uuid)))
    assert len(res_v1_combined.items) == 2
    names_v1 = {a.name for a in res_v1_combined.items}
    assert "Global WiFi" in names_v1
    assert "V1 Fireplace" in names_v1
    assert "V2 Hot Tub" not in names_v1

    # 3. Vendor 2 combined (global + vendor 2)
    res_v2_combined = await list_uc.execute(AmenityQueryDTO(vendor_id=str(vendor_2_uuid)))  # defaults to vendor_combined
    assert len(res_v2_combined.items) == 2
    names_v2 = {a.name for a in res_v2_combined.items}
    assert "Global WiFi" in names_v2
    assert "V2 Hot Tub" in names_v2
    assert "V1 Fireplace" not in names_v2

    # 4. All
    res_all = await list_uc.execute(AmenityQueryDTO(scope="all"))
    assert len(res_all.items) == 3


@pytest.mark.anyio
async def test_admin_list_facilities_scope_and_vendor():
    from app.application.dto.attributes.facility import FacilityQueryDTO
    from app.application.use_case.admin.attributes.attribute.get_facility_use_case import ListFacilitiesUseCase
    from app.models.facility_model import FacilityStatus

    service = InMemoryAttributeService(Facility)
    admin_user = SimpleNamespace(id=1, role="admin")
    vendor_1_uuid = uuid.uuid4()
    v1 = SimpleNamespace(id=10, public_id=vendor_1_uuid)

    class MockUserService:
        async def get_user_by_public_id(self, pid, flush=False):
            if str(pid) == str(vendor_1_uuid):
                return v1
            return None

        async def get_user_by_id(self, uid, flush=False):
            if uid == 10:
                return v1
            return None

    user_service = MockUserService()
    storage = SimpleNamespace()

    await service.create(Facility(name="Global Parking", vendor_id=None, status=FacilityStatus.ACTIVE))
    await service.create(Facility(name="V1 Gym", vendor_id=10, status=FacilityStatus.ACTIVE))

    list_uc = ListFacilitiesUseCase(service, storage, verify_csrf=False, current_user=admin_user, user_service=user_service)

    res_global = await list_uc.execute(FacilityQueryDTO(scope="global"))
    assert len(res_global.items) == 1
    assert res_global.items[0].name == "Global Parking"

    res_combined = await list_uc.execute(FacilityQueryDTO(vendor_id=str(vendor_1_uuid)))
    assert len(res_combined.items) == 2


@pytest.mark.anyio
async def test_admin_list_room_types_scope_and_vendor():
    from app.application.dto.attributes.room_type import RoomTypeQueryDTO
    from app.application.use_case.admin.attributes.attribute.get_room_type_use_case import ListRoomTypesUseCase
    from app.models.room_type_model import RoomTypeStatus

    service = InMemoryAttributeService(RoomType)
    admin_user = SimpleNamespace(id=1, role="admin")
    vendor_1_uuid = uuid.uuid4()
    v1 = SimpleNamespace(id=10, public_id=vendor_1_uuid)

    class MockUserService:
        async def get_user_by_public_id(self, pid, flush=False):
            if str(pid) == str(vendor_1_uuid):
                return v1
            return None

        async def get_user_by_id(self, uid, flush=False):
            if uid == 10:
                return v1
            return None

    user_service = MockUserService()

    await service.create(RoomType(name="Global Standard", capacity=2, vendor_id=None, status=RoomTypeStatus.ACTIVE))
    await service.create(RoomType(name="V1 Penthouse", capacity=4, vendor_id=10, status=RoomTypeStatus.ACTIVE))

    list_uc = ListRoomTypesUseCase(service, verify_csrf=False, current_user=admin_user, user_service=user_service)

    res_global = await list_uc.execute(RoomTypeQueryDTO(scope="global"))
    assert len(res_global.items) == 1
    assert res_global.items[0].name == "Global Standard"

    res_combined = await list_uc.execute(RoomTypeQueryDTO(vendor_id=str(vendor_1_uuid)))
    assert len(res_combined.items) == 2


def test_model_vendor_public_id_safety_against_missing_greenlet():
    from app.schemas.amenity_schema import AmenitySchema
    from app.schemas.facility_schema import FacilitySchema
    from app.schemas.room_type_schema import RoomTypeSchema
    from app.models.facility_model import FacilityStatus
    from app.models.room_type_model import RoomTypeStatus

    # Unpersisted or unloaded model instances without greenlet
    amenity = Amenity(name="Pool", status=AmenityStatus.ACTIVE, vendor_id=123, public_id=uuid.uuid4())
    facility = Facility(name="Spa", status=FacilityStatus.ACTIVE, vendor_id=123, public_id=uuid.uuid4())
    room_type = RoomType(name="Suite", capacity=3, status=RoomTypeStatus.ACTIVE, vendor_id=123, public_id=uuid.uuid4())

    s_amenity = AmenitySchema.model_validate(amenity, from_attributes=True)
    assert s_amenity.name == "Pool"
    assert s_amenity.vendor_id == "123"

    s_facility = FacilitySchema.model_validate(facility, from_attributes=True)
    assert s_facility.name == "Spa"
    assert s_facility.vendor_id == "123"

    s_room_type = RoomTypeSchema.model_validate(room_type, from_attributes=True)
    assert s_room_type.name == "Suite"
    assert s_room_type.vendor_id == "123"

    # When vendor relationship is loaded with public_id
    vendor_uuid = uuid.uuid4()
    amenity.vendor = SimpleNamespace(public_id=vendor_uuid)
    s_loaded = AmenitySchema.model_validate(amenity, from_attributes=True)
    assert s_loaded.vendor_id == str(vendor_uuid)


