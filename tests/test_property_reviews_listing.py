import asyncio
from unittest.mock import AsyncMock, MagicMock
import pytest
from app.application.dto.properties.public.property import PublicPropertyQueryDTO
from app.application.dto.properties.property import PropertyQueryDTO
from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
from app.application.use_case.public.property.get_properties_use_case import PublicPropertiesUseCase
from app.application.use_case.public.property.get_property_use_case import PublicGetPropertyUseCase
from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase
from app.application.use_case.admin.properties.get_properties_use_case import GetPropertiesUseCase
from app.application.use_case.vendor.property.get_properties_use_case import GetVendorPropertyUseCase
from app.models.property_model import Property, PropertyStatus, PropertyType
from app.repositories.base_repository import Page
from app.repositories.review_repository import ReviewRepository
from app.schemas.public.property_schema import PublicPropertySchema, PublicPropertyDetailResponse
from app.schemas.property_schema import PropertySchema


def test_review_repository_get_properties_rating_summary():
    async def run_test():
        db_mock = AsyncMock()
        # Mock result of query with multiple properties and ratings:
        # prop 1: two 5-star, one 4-star -> total 3, avg 4.67
        # prop 2: one 3-star -> total 1, avg 3.0
        rows = [
            (1, 5, 2),
            (1, 4, 1),
            (2, 3, 1),
        ]
        result_mock = MagicMock()
        result_mock.all.return_value = rows
        db_mock.execute.return_value = result_mock

        repo = ReviewRepository(db_mock)
        summary = await repo.get_properties_rating_summary([1, 2, 3])

        # Verify property 1
        assert summary[1]["total_reviews"] == 3
        assert summary[1]["average_rating"] == 4.67
        assert summary[1]["rating_distribution"]["5"] == 2
        assert summary[1]["rating_distribution"]["4"] == 1
        assert summary[1]["rating_distribution"]["1"] == 0

        # Verify property 2
        assert summary[2]["total_reviews"] == 1
        assert summary[2]["average_rating"] == 3.0
        assert summary[2]["rating_distribution"]["3"] == 1

        # Verify property 3 (no reviews)
        assert summary[3]["total_reviews"] == 0
        assert summary[3]["average_rating"] == 0.0
        assert summary[3]["rating_distribution"] == {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

        # Verify empty input
        empty_res = await repo.get_properties_rating_summary([])
        assert empty_res == {}

    asyncio.run(run_test())


def test_public_properties_use_case_with_reviews():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        storage_service.generate_presigned_url = AsyncMock(return_value="https://cdn.example.com/asset.jpg")
        city_service = AsyncMock()
        location_service = AsyncMock()
        review_service = AsyncMock()

        prop = MagicMock(spec=Property)
        prop.id = 10
        prop.public_id = "11111111-1111-1111-1111-111111111111"
        prop.name = "Hillside Villa"
        prop.slug = "hillside-villa"
        prop.currency = "INR"
        prop.type = PropertyType.VILLA
        prop.price_per_night = 5000.0
        prop.sale_per_night = 4500.0
        prop.address = "Main Road"
        prop.latitude = 31.10
        prop.longitude = 77.17
        prop.description = "Luxurious Villa"
        prop.status = PropertyStatus.ACTIVE
        prop.location = MagicMock(public_id="22222222-2222-2222-2222-222222222222", name="Mall Road")
        prop.city = MagicMock(public_id="33333333-3333-3333-3333-333333333333", name="Shimla")
        prop.property_assets = []

        fake_page = Page(items=[prop], total=1, page=1, page_size=10)
        property_service.list.return_value = fake_page

        review_service.get_properties_rating_summary.return_value = {
            10: {
                "average_rating": 4.8,
                "total_reviews": 15,
                "rating_distribution": {"1": 0, "2": 0, "3": 1, "4": 1, "5": 13},
            }
        }

        use_case = PublicPropertiesUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
            review_service=review_service,
        )

        dto = PublicPropertyQueryDTO(page=1, size=10)
        result_page = await use_case.execute(dto)

        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Hillside Villa"
        assert item["average_rating"] == 4.8
        assert item["total_reviews"] == 15
        assert item["rating_summary"]["average_rating"] == 4.8
        assert item["rating_summary"]["total_reviews"] == 15
        assert item["rating_summary"]["rating_distribution"]["5"] == 13

        # Validate with PublicPropertySchema
        schema_obj = PublicPropertySchema.model_validate(item)
        assert schema_obj.average_rating == 4.8
        assert schema_obj.total_reviews == 15
        assert schema_obj.rating_summary.total_reviews == 15

    asyncio.run(run_test())


def test_public_search_stays_use_case_with_reviews():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        storage_service.generate_presigned_url = AsyncMock(return_value="https://cdn.example.com/asset.jpg")
        city_service = AsyncMock()
        location_service = AsyncMock()
        review_service = AsyncMock()

        prop = MagicMock(spec=Property)
        prop.id = 20
        prop.public_id = "22222222-2222-2222-2222-222222222222"
        prop.name = "Riverside Cottage"
        prop.slug = "riverside-cottage"
        prop.currency = "INR"
        prop.type = PropertyType.COTTAGE
        prop.price_per_night = 3000.0
        prop.sale_per_night = 2800.0
        prop.address = "River Bank"
        prop.latitude = 32.10
        prop.longitude = 76.17
        prop.description = "Quiet Cottage"
        prop.status = PropertyStatus.ACTIVE
        prop.location = MagicMock(public_id="33333333-3333-3333-3333-333333333333", name="Old Town")
        prop.city = MagicMock(public_id="44444444-4444-4444-4444-444444444444", name="Manali")
        prop.property_assets = []

        fake_page = Page(items=[prop], total=1, page=1, page_size=10)
        property_service.search_stays.return_value = fake_page

        review_service.get_properties_rating_summary.return_value = {
            20: {
                "average_rating": 4.5,
                "total_reviews": 8,
                "rating_distribution": {"1": 0, "2": 0, "3": 1, "4": 2, "5": 5},
            }
        }

        use_case = PublicSearchStaysUseCase(
            property_service=property_service,
            storage_service=storage_service,
            city_service=city_service,
            location_service=location_service,
            review_service=review_service,
        )

        dto = PublicSearchStaysQueryDTO(city="Manali")
        result_page = await use_case.execute(dto)

        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Riverside Cottage"
        assert item["average_rating"] == 4.5
        assert item["total_reviews"] == 8

        # Validate with PublicPropertySchema
        schema_obj = PublicPropertySchema.model_validate(item)
        assert schema_obj.average_rating == 4.5
        assert schema_obj.total_reviews == 8

    asyncio.run(run_test())


def test_public_get_property_use_case_with_reviews():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        storage_service.generate_presigned_url = AsyncMock(return_value="https://cdn.example.com/asset.jpg")
        booking_service = AsyncMock()
        review_service = AsyncMock()

        prop = MagicMock(spec=Property)
        prop.id = 30
        prop.public_id = "33333333-3333-3333-3333-333333333333"
        prop.name = "Mountain Retreat"
        prop.slug = "mountain-retreat"
        prop.currency = "INR"
        prop.type = PropertyType.RESORT
        prop.price_per_night = 6000.0
        prop.sale_per_night = 5500.0
        prop.address = "Ridge"
        prop.latitude = 32.20
        prop.longitude = 76.30
        prop.description = "Peaceful Resort"
        prop.status = PropertyStatus.ACTIVE
        prop.is_featured = True
        prop.vendor = MagicMock(public_id="55555555-5555-5555-5555-555555555555", full_name="John Doe", email="john@example.com", is_profile_image_url=None)
        prop.location = MagicMock(public_id="66666666-6666-6666-6666-666666666666", name="Ridge View")
        prop.city = MagicMock(public_id="77777777-7777-7777-7777-777777777777", name="Shimla")
        prop.property_room_types = []
        prop.property_amenities = []
        prop.property_facilities = []
        prop.property_food_options = []
        prop.property_assets = []

        property_service.get_by_slug.return_value = prop
        review_service.get_property_rating_summary.return_value = {
            "average_rating": 4.9,
            "total_reviews": 50,
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 5, "5": 45},
        }

        use_case = PublicGetPropertyUseCase(
            property_service=property_service,
            storage_service=storage_service,
            booking_service=booking_service,
            review_service=review_service,
        )

        result = await use_case.execute("mountain-retreat")
        assert result["name"] == "Mountain Retreat"
        assert result["average_rating"] == 4.9
        assert result["total_reviews"] == 50
        assert result["rating_summary"]["total_reviews"] == 50

        # Validate with PublicPropertyDetailResponse
        schema_obj = PublicPropertyDetailResponse.model_validate(result)
        assert schema_obj.average_rating == 4.9
        assert schema_obj.total_reviews == 50

    asyncio.run(run_test())


def test_admin_get_properties_use_case_with_reviews():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        user_service = AsyncMock()
        current_user = MagicMock(id=1)
        review_service = AsyncMock()

        prop = MagicMock(spec=Property)
        prop.id = 40
        prop.public_id = "44444444-4444-4444-4444-444444444444"
        prop.name = "Admin Property"
        prop.slug = "admin-property"
        prop.currency = "INR"
        prop.type = PropertyType.HOTEL
        prop.price_per_night = 4000.0
        prop.sale_per_night = 3800.0
        prop.address = "Downtown"
        prop.latitude = 30.0
        prop.longitude = 75.0
        prop.description = "Centrally located"
        prop.status = PropertyStatus.ACTIVE
        prop.is_featured = False
        prop.vendor = MagicMock(public_id="88888888-8888-8888-8888-888888888888", full_name="Admin Host", email="host@example.com")
        prop.location = MagicMock(public_id="99999999-9999-9999-9999-999999999999", name="City Center")
        prop.city = MagicMock(public_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", name="Delhi")
        prop.property_room_types = []
        prop.property_amenities = []
        prop.property_facilities = []
        prop.property_food_options = []
        prop.property_assets = []

        fake_page = Page(items=[prop], total=1, page=1, page_size=10)
        property_service.list.return_value = fake_page

        review_service.get_properties_rating_summary.return_value = {
            40: {
                "average_rating": 4.2,
                "total_reviews": 10,
                "rating_distribution": {"1": 0, "2": 1, "3": 1, "4": 3, "5": 5},
            }
        }

        use_case = GetPropertiesUseCase(
            property_service=property_service,
            storage_service=storage_service,
            user_service=user_service,
            current_user=current_user,
            review_service=review_service,
        )

        dto = PropertyQueryDTO(page=1, size=10)
        result_page = await use_case.execute(dto)

        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Admin Property"
        assert item["average_rating"] == 4.2
        assert item["total_reviews"] == 10

        # Validate with PropertySchema
        schema_obj = PropertySchema.model_validate(item)
        assert schema_obj.average_rating == 4.2
        assert schema_obj.total_reviews == 10

    asyncio.run(run_test())


def test_vendor_get_properties_use_case_with_reviews():
    async def run_test():
        property_service = AsyncMock()
        storage_service = AsyncMock()
        current_user = MagicMock(id=5)
        review_service = AsyncMock()

        prop = MagicMock(spec=Property)
        prop.id = 50
        prop.public_id = "55555555-5555-5555-5555-555555555555"
        prop.name = "Vendor Homestay"
        prop.slug = "vendor-homestay"
        prop.currency = "INR"
        prop.type = PropertyType.HOME_STAY
        prop.price_per_night = 2000.0
        prop.sale_per_night = 1800.0
        prop.address = "Village Road"
        prop.latitude = 32.5
        prop.longitude = 76.5
        prop.description = "Peaceful Village Homestay"
        prop.status = PropertyStatus.ACTIVE
        prop.is_featured = False
        prop.location = MagicMock(public_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", name="Village")
        prop.city = MagicMock(public_id="cccccccc-cccc-cccc-cccc-cccccccccccc", name="Dharamshala")
        prop.property_room_types = []
        prop.property_amenities = []
        prop.property_facilities = []
        prop.property_food_options = []
        prop.property_assets = []

        fake_page = Page(items=[prop], total=1, page=1, page_size=10)
        property_service.list.return_value = fake_page

        review_service.get_properties_rating_summary.return_value = {
            50: {
                "average_rating": 4.95,
                "total_reviews": 22,
                "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 1, "5": 21},
            }
        }

        use_case = GetVendorPropertyUseCase(
            property_service=property_service,
            storage_service=storage_service,
            verify_csrf=True,
            current_user=current_user,
            review_service=review_service,
        )

        dto = PropertyQueryDTO(page=1, size=10)
        result_page = await use_case.execute(dto)

        assert len(result_page.items) == 1
        item = result_page.items[0]
        assert item["name"] == "Vendor Homestay"
        assert item["average_rating"] == 4.95
        assert item["total_reviews"] == 22

        # Validate with PropertySchema
        schema_obj = PropertySchema.model_validate(item)
        assert schema_obj.average_rating == 4.95
        assert schema_obj.total_reviews == 22

    asyncio.run(run_test())

