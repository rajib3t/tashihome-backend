import asyncio
import io
import json
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from app.application.dto.assistant.assistant import (
    AssistantChatRequestDTO,
    AssistantCheckoutDTO,
    AssistantSearchDTO,
)
from app.application.use_case.public.assistant.chat_assistant_use_case import ChatAssistantUseCase
from app.core.config import settings
from app.deps.auth import CurrentUser
from app.mcp.protocol import JSONRPCRequest
from app.mcp.prompts import MCPPromptHandler
from app.mcp.resources import MCPResourceHandler
from app.mcp.server import TashiHomeMCPServer
from app.mcp.tools import MCPToolExecutor
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.city_model import City, CityStatus
from app.models.country_model import Country, CountryStatus
from app.models.location_model import Location, LocationStatus
from app.models.property_model import Property, PropertyStatus, PropertyType
from app.models.property_room_type_model import PropertyRoomType
from app.models.property_room_type_price_model import PropertyRoomTypePrice
from app.models.review_model import Review, ReviewStatus
from app.models.room_type_model import RoomType, RoomTypeStatus
from app.models.user_model import User, UserRole, UserStatus
from app.repositories.base_repository import Page
from app.services.assistant_service import AssistantService
from app.services.embedding_service import EmbeddingService

try:
    import pytest
    _fixture = pytest.fixture
except ImportError:
    def _fixture(fn):
        return fn


@_fixture
def mock_domain_services():
    prop_service = AsyncMock()
    prop_service.search_stays = AsyncMock(return_value=Page(items=[], total=0, page=1, page_size=10))
    prop_service.get_all = AsyncMock(return_value=Page(items=[], total=0, page=1, page_size=10))
    booking_service = MagicMock()
    booking_service.check_availability = AsyncMock()
    booking_service.calculate_pricing_quote = MagicMock()
    booking_service.generate_booking_reference = MagicMock(return_value="BK-20260908-TEST")
    booking_service.create_booking = AsyncMock()
    booking_service.get_by_reference = AsyncMock()
    booking_service.get_booking_by_identifier = AsyncMock(side_effect=lambda ref, *a, **k: booking_service.get_by_reference(ref, *a, **k))
    booking_service.get_by_public_id = AsyncMock()
    booking_service.get_by_id = AsyncMock()
    booking_service.cancel_booking = AsyncMock()

    user_service = AsyncMock()
    payment_service = AsyncMock()
    payment_service.create = AsyncMock()
    razorpay_service = MagicMock()
    razorpay_service.is_configured = MagicMock(return_value=False)
    razorpay_service.create_order = AsyncMock()

    c_thimphu = City(id=1, public_id=uuid4(), name="Thimphu", slug="thimphu", is_featured=True, status=CityStatus.ACTIVE)
    c_paro = City(id=2, public_id=uuid4(), name="Paro", slug="paro", is_featured=True, status=CityStatus.ACTIVE)
    c_punakha = City(id=3, public_id=uuid4(), name="Punakha", slug="punakha", is_featured=True, status=CityStatus.ACTIVE)
    default_cities = [c_thimphu, c_paro, c_punakha]

    city_service = AsyncMock()
    city_service.get_all = AsyncMock(return_value=default_cities)
    city_service.get_city_with_is_featured = AsyncMock(return_value=default_cities)

    def _find_city_by_name(name, **kw):
        pool = city_service.get_all.return_value or city_service.get_city_with_is_featured.return_value or default_cities
        items = getattr(pool, "items", pool) or []
        return next((c for c in items if getattr(c, "name", "").lower() == (name or "").lower()), None)

    def _find_city_by_slug(slug, **kw):
        pool = city_service.get_all.return_value or city_service.get_city_with_is_featured.return_value or default_cities
        items = getattr(pool, "items", pool) or []
        return next((c for c in items if getattr(c, "slug", "").lower() == (slug or "").lower()), None)

    city_service.get_by_name.side_effect = _find_city_by_name
    city_service.get_by_slug.side_effect = _find_city_by_slug

    location_service = AsyncMock()
    location_service.list = AsyncMock(return_value=Page(items=[], total=0, page=1, page_size=100))
    location_service.get_by_name = AsyncMock(return_value=None)
    location_service.get_by_slug = AsyncMock(return_value=None)

    country_service = AsyncMock()
    country_service.get_all = AsyncMock(return_value=[])
    room_type_service = AsyncMock()
    tax_service = AsyncMock()
    setting_service = AsyncMock()
    setting_service.get_by_key = AsyncMock(return_value=None)
    setting_service.get_value = AsyncMock(return_value=None)
    review_service = AsyncMock()
    review_service.get_properties_rating_summary = AsyncMock(return_value={})
    review_service.get_property_rating_summary = AsyncMock(return_value={"average_rating": 0.0, "total_reviews": 0, "distribution": {}, "recent_reviews": []})
    review_service.list_by_property = AsyncMock(return_value=Page(items=[], total=0, page=1, page_size=5))
    review_service.get_recent_reviews = AsyncMock(return_value=[])
    event_bus = AsyncMock()

    executor = MCPToolExecutor(
        property_service=prop_service,
        booking_service=booking_service,
        user_service=user_service,
        payment_service=payment_service,
        razorpay_service=razorpay_service,
        city_service=city_service,
        location_service=location_service,
        country_service=country_service,
        room_type_service=room_type_service,
        tax_service=tax_service,
        setting_service=setting_service,
        review_service=review_service,
        event_bus=event_bus,
    )

    settings.PAYMENT_ENABLED = True
    return {
        "prop_service": prop_service,
        "booking_service": booking_service,
        "user_service": user_service,
        "payment_service": payment_service,
        "razorpay_service": razorpay_service,
        "city_service": city_service,
        "location_service": location_service,
        "country_service": country_service,
        "tax_service": tax_service,
        "setting_service": setting_service,
        "review_service": review_service,
        "event_bus": event_bus,
        "executor": executor,
    }


def test_mcp_tool_search_homestays(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
            type=PropertyType.HOME_STAY,
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=1,
            page=1,
            page_size=10,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {
            1: {"average_rating": 4.9, "total_reviews": 12}
        }

        result = await svc["executor"].execute_tool(
            "search_homestays",
            {"query": "Thimphu", "guests": 2, "rooms": 1},
        )

        assert result.isError is False
        assert result.data["total"] == 1
        assert result.data["properties"][0]["name"] == "Bhutan Heritage Homestay"
        assert result.data["properties"][0]["base_price"] == 3500.0
        assert result.data["properties"][0]["rating"] == 4.9

    asyncio.run(run_test())


def test_mcp_tool_check_availability(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Paro Scenic Retreat",
            slug="paro-scenic-retreat",
            status=PropertyStatus.ACTIVE,
            price_per_night=4000.0,
            currency="BTN",
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 3,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 2,
            "price_per_night": 4000.0,
            "subtotal": 8000.0,
            "discount_amount": 0.0,
            "tax_amount": 400.0,
            "total_amount": 8400.0,
            "currency": "BTN",
        }

        today = date.today()
        cin = (today + timedelta(days=5)).isoformat()
        cout = (today + timedelta(days=7)).isoformat()

        result = await svc["executor"].execute_tool(
            "check_stay_availability",
            {
                "property_id": "paro-scenic-retreat",
                "check_in_date": cin,
                "check_out_date": cout,
                "num_guests": 2,
            },
        )

        assert result.isError is False
        assert result.data["is_available"] is True
        assert result.data["total_amount"] == 8400.0
        assert result.data["num_nights"] == 2

    asyncio.run(run_test())


def test_mcp_tool_checkout_and_auto_register_guest(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Punakha River View",
            slug="punakha-river-view",
            status=PropertyStatus.ACTIVE,
            price_per_night=3000.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 2,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 3,
            "price_per_night": 3000.0,
            "subtotal": 9000.0,
            "discount_amount": 0.0,
            "tax_amount": 450.0,
            "total_amount": 9450.0,
            "currency": "BTN",
        }

        # User does not exist initially
        svc["user_service"].get_user_by_email.return_value = None
        new_user = User(
            id=42,
            public_id=uuid4(),
            full_name="Sonam Tashi",
            email="sonam@test.com",
            phone="+97517001122",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        svc["user_service"].create_user.return_value = new_user
        svc["user_service"].get_user_by_id.return_value = new_user

        created_booking = Booking(
            id=101,
            public_id=uuid4(),
            booking_reference="BK-20260908-TEST",
            guest_id=42,
            property_id=1,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=10),
            check_out_date=date.today() + timedelta(days=13),
            num_guests=2,
            num_rooms=1,
            total_amount=9450.0,
            currency="BTN",
        )
        svc["booking_service"].create_booking.return_value = created_booking

        today = date.today()
        cin = (today + timedelta(days=10)).isoformat()
        cout = (today + timedelta(days=13)).isoformat()

        # Execute checkout without authenticated user ID
        result = await svc["executor"].execute_tool(
            "checkout_and_book",
            {
                "property_id": "punakha-river-view",
                "check_in_date": cin,
                "check_out_date": cout,
                "num_guests": 2,
                "num_rooms": 1,
                "guest_name": "Sonam Tashi",
                "guest_email": "sonam@test.com",
                "guest_phone": "+97517001122",
            },
            current_user_id=None,
        )

        assert result.isError is False
        assert result.data["booking_reference"] == "BK-20260908-TEST"
        assert result.data["total_amount"] == 9450.0
        assert result.data["guest"]["email"] == "sonam@test.com"
        assert svc["user_service"].create_user.called
        assert svc["booking_service"].create_booking.called

    asyncio.run(run_test())


def test_mcp_server_jsonrpc_protocol(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        city_thimphu = City(id=1, name="Thimphu", slug="thimphu", is_featured=True, status=CityStatus.ACTIVE)
        svc["city_service"].get_city_with_is_featured.return_value = [city_thimphu]
        svc["city_service"].get_all.return_value = [city_thimphu]

        server = TashiHomeMCPServer(
            tool_executor=svc["executor"],
            resource_handler=MCPResourceHandler(
                city_service=svc["city_service"],
                country_service=svc["country_service"],
            ),
            prompt_handler=MCPPromptHandler(),
        )

        # 1. Test initialize
        init_req = {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
        init_res = await server.handle_jsonrpc(init_req)
        assert init_res["id"] == 1
        assert init_res["result"]["serverInfo"]["name"] == "tashihome-mcp-server"

        # 2. Test tools/list
        tools_req = {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}}
        tools_res = await server.handle_jsonrpc(tools_req)
        assert tools_res["id"] == 2
        tool_names = [t["name"] for t in tools_res["result"]["tools"]]
        assert "search_homestays" in tool_names
        assert "check_stay_availability" in tool_names
        assert "checkout_and_book" in tool_names
        assert "register_guest_user" in tool_names

        # 3. Test resources/list & read
        res_list_req = {"jsonrpc": "2.0", "id": 3, "method": "resources/list", "params": {}}
        res_list_res = await server.handle_jsonrpc(res_list_req)
        assert len(res_list_res["result"]["resources"]) >= 2

        read_res_req = {"jsonrpc": "2.0", "id": 4, "method": "resources/read", "params": {"uri": "tashihome://destinations"}}
        read_res_res = await server.handle_jsonrpc(read_res_req)
        assert "Thimphu" in read_res_res["result"]["contents"][0]["text"]

        # 4. Test prompts/list
        prompts_req = {"jsonrpc": "2.0", "id": 5, "method": "prompts/list", "params": {}}
        prompts_res = await server.handle_jsonrpc(prompts_req)
        prompt_names = [p["name"] for p in prompts_res["result"]["prompts"]]
        assert "homestay_trip_planner" in prompt_names
        assert "booking_concierge" in prompt_names

    asyncio.run(run_test())


def test_assistant_chat_use_case_fallback_flow(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Thimphu Valley Homestay",
            slug="thimphu-valley-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3200.0,
            currency="BTN",
            type=PropertyType.HOME_STAY,
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=1,
            page=1,
            page_size=10,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {
            1: {"average_rating": 4.8, "total_reviews": 8}
        }

        assistant_service = AssistantService(tool_executor=svc["executor"])
        assistant_service.gemini_key = None
        assistant_service.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant_service)

        # 1. Greeting message
        greeting_req = AssistantChatRequestDTO(message="Hello")
        greeting_resp = await use_case.execute(greeting_req)
        assert greeting_resp.intent == "greeting"
        assert greeting_resp.reply is not None and len(greeting_resp.reply) > 0

        # 2. Search Query
        req = AssistantChatRequestDTO(message="Find me homestays in Thimphu for 2 guests")
        resp = await use_case.execute(req)
        assert resp.reply is not None
        assert "Thimphu" in resp.reply or "homestay" in resp.reply.lower()
        assert resp.search_results is not None
        assert len(resp.search_results) == 1

        # 3. Search Query for destination outside or not found
        darj_req = AssistantChatRequestDTO(message="find homestay darjelling")
        darj_resp = await use_case.execute(darj_req)
        assert darj_resp.intent == "search_homestays"
        assert len(darj_resp.tool_calls) == 1
        assert darj_resp.tool_calls[0].tool == "search_homestays"
        assert "darj" in darj_resp.tool_calls[0].arguments.get("query", "").lower()

        # 4. Suggestions list
        assert len(resp.suggested_actions) > 0

    asyncio.run(run_test())


def test_mcp_checkout_generates_payment_gateway(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Punakha River View",
            slug="punakha-river-view",
            status=PropertyStatus.ACTIVE,
            price_per_night=3000.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 2,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 2,
            "price_per_night": 3000.0,
            "subtotal": 6000.0,
            "discount_amount": 0.0,
            "tax_amount": 300.0,
            "total_amount": 6300.0,
            "currency": "BTN",
        }

        user = User(
            id=10,
            public_id=uuid4(),
            full_name="Karma Dorji",
            email="karma@test.com",
            phone="+97517112233",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        svc["user_service"].get_user_by_email.return_value = user
        svc["user_service"].get_user_by_id.return_value = user

        created_booking = Booking(
            id=55,
            public_id=uuid4(),
            booking_reference="BK-20260908-TEST",
            guest_id=10,
            property_id=1,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=7),
            num_guests=2,
            num_rooms=1,
            total_amount=6300.0,
            currency="BTN",
        )
        svc["booking_service"].create_booking.return_value = created_booking

        today = date.today()
        cin = (today + timedelta(days=5)).isoformat()
        cout = (today + timedelta(days=7)).isoformat()

        result = await svc["executor"].execute_tool(
            "checkout_and_book",
            {
                "property_id": "punakha-river-view",
                "check_in_date": cin,
                "check_out_date": cout,
                "num_guests": 2,
                "num_rooms": 1,
                "guest_name": "Karma Dorji",
                "guest_email": "karma@test.com",
                "guest_phone": "+97517112233",
            },
            current_user_id=10,
        )

        assert result.isError is False
        assert "payment_gateway" in result.data
        gw = result.data["payment_gateway"]
        assert gw["gateway"] == "razorpay"
        assert gw["order_id"].startswith("order_")
        assert gw["amount"] == 6300.0
        assert gw["currency"] == "BTN"
        assert "pay" in gw["payment_url"]
        assert gw["status"] == "initiated"
        assert svc["payment_service"].create.called

    asyncio.run(run_test())


def test_mcp_initiate_booking_payment(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        booking = Booking(
            id=77,
            public_id=uuid4(),
            booking_reference="BK-20260908-PAY",
            guest_id=10,
            property_id=1,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=7),
            num_guests=2,
            num_rooms=1,
            total_amount=5000.0,
            currency="INR",
            payments=[],
        )
        svc["booking_service"].get_by_reference.return_value = booking

        result = await svc["executor"].execute_tool(
            "initiate_booking_payment",
            {
                "booking_reference": "BK-20260908-PAY",
                "payment_method": "card",
            },
            current_user_id=10,
        )

        assert result.isError is False
        assert result.data["booking_reference"] == "BK-20260908-PAY"
        assert result.data["total_amount"] == 5000.0
        assert result.data["remaining_balance"] == 5000.0
        assert "payment_gateway" in result.data
        assert result.data["payment_gateway"]["amount"] == 5000.0
        assert result.data["payment_gateway"]["currency"] == "INR"
        assert "BK-20260908-PAY" in result.data["payment_gateway"]["payment_url"]

    asyncio.run(run_test())


def test_mcp_search_homestays_location_and_address(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Motithang Peaceful Homestay",
            slug="motithang-peaceful-homestay",
            address="Norzin Lam 4, Motithang",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
            type=PropertyType.HOME_STAY,
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=1,
            page=1,
            page_size=10,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {}

        result = await svc["executor"].execute_tool(
            "search_homestays",
            {
                "query": "Thimphu",
                "location_name": "Motithang",
                "address": "Norzin Lam",
            },
        )

        assert result.isError is False
        assert result.data["total"] == 1
        assert result.data["properties"][0]["address"] == "Norzin Lam 4, Motithang"
        # Verify kwargs passed to search_stays
        call_kwargs = svc["prop_service"].search_stays.call_args[1]
        assert call_kwargs["location_name"] == "Motithang"
        assert call_kwargs["address"] == "Norzin Lam"

    asyncio.run(run_test())


def test_assistant_chat_payment_intent(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        booking = Booking(
            id=88,
            public_id=uuid4(),
            booking_reference="BK-20260908-TEST",
            guest_id=10,
            property_id=1,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=7),
            num_guests=2,
            num_rooms=1,
            total_amount=4500.0,
            currency="BTN",
            payments=[],
        )
        svc["booking_service"].get_by_reference.return_value = booking

        assistant_service = AssistantService(tool_executor=svc["executor"])
        assistant_service.gemini_key = None
        assistant_service.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant_service)

        req = AssistantChatRequestDTO(message="Please give me payment link to pay for booking BK-20260908-TEST")
        resp = await use_case.execute(req)

        assert resp.intent == "initiate_booking_payment"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool == "initiate_booking_payment"
        assert "Payment Gateway" in resp.reply or "BK-20260908-TEST" in resp.reply
        assert resp.booking is None or resp.reply is not None

    asyncio.run(run_test())


def test_mcp_room_type_resolution_and_pricing(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt_deluxe_uuid = uuid4()
        rt_standard_uuid = uuid4()

        rt_deluxe = RoomType(id=10, public_id=rt_deluxe_uuid, name="Deluxe Mountain Room", capacity=3, status=RoomTypeStatus.ACTIVE)
        rt_standard = RoomType(id=20, public_id=rt_standard_uuid, name="Standard Cozy Room", capacity=2, status=RoomTypeStatus.ACTIVE)

        prt_deluxe = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=1,
            room_type_id=10,
            total_units=2,
            price_per_night=5000.0,
            sale_per_night=4500.0,
        )
        prt_deluxe.room_type = rt_deluxe

        prt_standard = PropertyRoomType(
            id=102,
            public_id=uuid4(),
            property_id=1,
            room_type_id=20,
            total_units=4,
            price_per_night=3000.0,
            sale_per_night=0.0,
        )
        prt_standard.room_type = rt_standard

        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3000.0,
            currency="BTN",
        )
        prop.property_room_types = [prt_deluxe, prt_standard]

        executor = svc["executor"]

        # Test room resolution by UUID
        res_uuid = await executor._resolve_room_type(prop, str(rt_deluxe_uuid))
        assert res_uuid == 10

        # Test room resolution by integer ID
        res_int = await executor._resolve_room_type(prop, 20)
        assert res_int == 20

        # Test room resolution by partial/case-insensitive name
        res_name = await executor._resolve_room_type(prop, "deluxe")
        assert res_name == 10

        res_standard_name = await executor._resolve_room_type(prop, "standard cozy")
        assert res_standard_name == 20

    asyncio.run(run_test())


def test_mcp_check_availability_returns_room_types_breakdown(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt_deluxe = RoomType(id=10, public_id=uuid4(), name="Deluxe Mountain Room", capacity=3, status=RoomTypeStatus.ACTIVE)
        rt_standard = RoomType(id=20, public_id=uuid4(), name="Standard Room", capacity=2, status=RoomTypeStatus.ACTIVE)

        prt_deluxe = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=1,
            room_type_id=10,
            total_units=2,
            price_per_night=5000.0,
            sale_per_night=4500.0,
        )
        prt_deluxe.room_type = rt_deluxe

        prt_standard = PropertyRoomType(
            id=102,
            public_id=uuid4(),
            property_id=1,
            room_type_id=20,
            total_units=3,
            price_per_night=3000.0,
            sale_per_night=0.0,
        )
        prt_standard.room_type = rt_standard

        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3000.0,
            currency="BTN",
        )
        prop.property_room_types = [prt_deluxe, prt_standard]
        svc["prop_service"].get_by_slug.return_value = prop

        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 2,
            "room_types_availability": [],
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 3,
            "price_per_night": 4500.0,
            "subtotal": 13500.0,
            "discount_amount": 0.0,
            "tax_amount": 675.0,
            "total_amount": 14175.0,
            "currency": "BTN",
        }

        today = date.today()
        cin = (today + timedelta(days=5)).isoformat()
        cout = (today + timedelta(days=8)).isoformat()

        result = await svc["executor"].execute_tool(
            "check_stay_availability",
            {
                "property_id": "bhutan-heritage-homestay",
                "check_in_date": cin,
                "check_out_date": cout,
                "room_type_id": "deluxe",
            },
        )

        assert result.isError is False
        assert result.data["is_available"] is True
        assert result.data["selected_room_type"] == "Deluxe Mountain Room"
        assert result.data["price_per_night"] == 4500.0
        assert len(result.data["room_types"]) == 2
        assert result.data["room_types"][0]["price_per_night"] == 4500.0
        assert result.data["room_types"][1]["price_per_night"] == 3000.0

    asyncio.run(run_test())


def test_assistant_chat_checkout_prompts_room_types_when_missing_dates(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt_deluxe = RoomType(id=10, public_id=uuid4(), name="Deluxe Suite", capacity=4, status=RoomTypeStatus.ACTIVE)
        rt_std = RoomType(id=20, public_id=uuid4(), name="Standard Room", capacity=2, status=RoomTypeStatus.ACTIVE)

        prt_deluxe = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=1,
            room_type_id=10,
            total_units=2,
            price_per_night=6000.0,
            sale_per_night=0.0,
        )
        prt_deluxe.room_type = rt_deluxe

        prt_std = PropertyRoomType(
            id=102,
            public_id=uuid4(),
            property_id=1,
            room_type_id=20,
            total_units=5,
            price_per_night=3500.0,
            sale_per_night=0.0,
        )
        prt_std.room_type = rt_std

        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
        )
        prop.property_room_types = [prt_deluxe, prt_std]
        svc["prop_service"].get_by_slug.return_value = prop

        assistant_service = AssistantService(tool_executor=svc["executor"])
        assistant_service.gemini_key = None
        assistant_service.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant_service)

        # User asks to checkout without specifying dates
        req = AssistantChatRequestDTO(message="I want to checkout Bhutan Heritage Homestay")
        resp = await use_case.execute(req)

        assert resp.intent == "checkout_and_book"
        assert "Available Room Types &" in resp.reply
        assert "Deluxe Suite" in resp.reply
        assert "Standard Room" in resp.reply
        assert "6000" in resp.reply
        assert "3500" in resp.reply
        assert "Check-in & Check-out dates" in resp.reply
        assert "Preferred Room Type" in resp.reply

    asyncio.run(run_test())


def test_assistant_chat_checkout_with_room_type_and_dates(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt_deluxe = RoomType(id=10, public_id=uuid4(), name="Deluxe Room", capacity=3, status=RoomTypeStatus.ACTIVE)
        prt_deluxe = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=1,
            room_type_id=10,
            total_units=2,
            price_per_night=5500.0,
            sale_per_night=0.0,
        )
        prt_deluxe.room_type = rt_deluxe

        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        prop.property_room_types = [prt_deluxe]
        svc["prop_service"].get_by_slug.return_value = prop

        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 2,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 3,
            "price_per_night": 5500.0,
            "subtotal": 16500.0,
            "discount_amount": 0.0,
            "tax_amount": 825.0,
            "total_amount": 17325.0,
            "currency": "BTN",
        }

        user = User(
            id=5,
            public_id=uuid4(),
            full_name="Dorji Wangchuk",
            email="dorji@tashihomes.in",
            phone="+97517123456",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        svc["user_service"].get_user_by_email.return_value = user
        svc["user_service"].get_user_by_id.return_value = user

        created_booking = Booking(
            id=99,
            public_id=uuid4(),
            booking_reference="BK-20260908-DELUXE",
            guest_id=5,
            property_id=1,
            room_type_id=10,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=8),
            num_guests=2,
            num_rooms=1,
            total_amount=17325.0,
            currency="BTN",
        )
        svc["booking_service"].create_booking.return_value = created_booking

        assistant_service = AssistantService(tool_executor=svc["executor"])
        assistant_service.gemini_key = None
        assistant_service.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant_service)

        cin = (date.today() + timedelta(days=5)).isoformat()
        cout = (date.today() + timedelta(days=8)).isoformat()

        req = AssistantChatRequestDTO(
            message=f"Book Bhutan Heritage Homestay Deluxe Room from {cin} to {cout} for 2 guests"
        )
        resp = await use_case.execute(req)

        assert resp.intent == "checkout_and_book"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool == "checkout_and_book"
        assert "BK-20260908-DELUXE" in resp.reply
        assert "Deluxe Room" in resp.reply
        assert "Payment Gateway & Checkout" in resp.reply

    asyncio.run(run_test())


def test_mcp_read_resource_featured_cities_from_database(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        city1 = City(
            id=1,
            public_id=uuid4(),
            name="Thimphu",
            slug="thimphu",
            tag_line="The Kingdom's Capital",
            short_description="A bustling blend of tradition and modernity.",
            is_featured=True,
            status=CityStatus.ACTIVE,
        )
        city2 = City(
            id=2,
            public_id=uuid4(),
            name="Paro",
            slug="paro",
            tag_line="Sacred Valley of Tiger's Nest",
            short_description="Home to the famous Taktsang monastery.",
            is_featured=True,
            status=CityStatus.ACTIVE,
        )

        svc["city_service"].get_city_with_is_featured.return_value = [city1, city2]
        svc["city_service"].get_by_slug.side_effect = None
        svc["city_service"].get_by_slug.return_value = city1

        handler = MCPResourceHandler(city_service=svc["city_service"])

        # 1. Read featured-cities resource
        res_featured = await handler.read_resource("tashihome://featured-cities")
        assert len(res_featured.contents) == 1
        assert "Thimphu" in res_featured.contents[0].text
        assert "The Kingdom's Capital" in res_featured.contents[0].text
        assert "Paro" in res_featured.contents[0].text

        # 2. Read destinations resource (fetches from database)
        res_destinations = await handler.read_resource("tashihome://destinations")
        assert len(res_destinations.contents) == 1
        assert "Thimphu" in res_destinations.contents[0].text
        assert "Paro" in res_destinations.contents[0].text

        # 3. Read specific city by slug
        res_single = await handler.read_resource("tashihome://cities/thimphu")
        assert len(res_single.contents) == 1
        assert "Thimphu" in res_single.contents[0].text
        assert "The Kingdom's Capital" in res_single.contents[0].text

    asyncio.run(run_test())


def test_assistant_chat_search_with_address_and_pagination(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            address="Norzin Lam 4, Thimphu",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=12,
            page=2,
            page_size=5,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {}

        assistant_service = AssistantService(tool_executor=svc["executor"])
        assistant_service.gemini_key = None
        assistant_service.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant_service)

        # 1. Search with address and page number
        req = AssistantChatRequestDTO(message="search homestays in Thimphu at address Norzin Lam page 2")
        resp = await use_case.execute(req)

        assert resp.intent == "search_homestays"
        assert len(resp.tool_calls) == 1
        tool_args = resp.tool_calls[0].arguments
        assert tool_args.get("page") == 2
        assert "norzin lam" in (tool_args.get("address") or "").lower()
        assert "Page 2 of 3" in resp.reply
        assert "Norzin Lam 4, Thimphu" in resp.reply

    asyncio.run(run_test())


def test_public_search_stays_use_case_address_and_pagination(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Changzamtog Pine Stay",
            slug="changzamtog-pine-stay",
            address="Changzamtog Express Way",
            status=PropertyStatus.ACTIVE,
            price_per_night=2800.0,
            currency="BTN",
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=8,
            page=1,
            page_size=4,
        )

        from app.application.dto.stays.public.stay import PublicSearchStaysQueryDTO
        from app.application.use_case.public.stay.search_stays_use_case import PublicSearchStaysUseCase

        storage_service = AsyncMock()
        use_case = PublicSearchStaysUseCase(
            property_service=svc["prop_service"],
            storage_service=storage_service,
            city_service=svc["city_service"],
            location_service=svc["location_service"],
            review_service=svc["review_service"],
        )

        dto = PublicSearchStaysQueryDTO(
            region="Thimphu",
            address="Changzamtog",
            page=1,
            page_size=4,
        )

        result_page = await use_case.execute(dto)
        assert result_page.total == 8
        assert len(result_page.items) == 1

        call_kwargs = svc["prop_service"].search_stays.call_args[1]
        assert call_kwargs["address"] == "Changzamtog"
        assert call_kwargs["page_size"] == 4

    asyncio.run(run_test())


def test_setting_driven_currency_and_symbol(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        svc["setting_service"].get_value.side_effect = lambda key, default=None: {
            "default_currency": "BTN",
            "currency_symbol": "Nu.",
            "app_date_format": "DD/MM/YYYY",
        }.get(key, default)

        prop = Property(
            id=10,
            public_id=uuid4(),
            vendor_id=1,
            name="Thimphu Valley Homestay",
            slug="thimphu-valley-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3200.0,
            currency="BTN",
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=1,
            page=1,
            page_size=10,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {
            10: {"average_rating": 4.7, "total_reviews": 5}
        }

        res = await svc["executor"].execute_tool("search_homestays", {"query": "Thimphu"})
        assert res.isError is False
        item = res.data["properties"][0]
        assert item["currency"] == "BTN"
        assert item["currency_symbol"] == "Nu."
        assert item["rating"] == 4.7
        assert item["review_count"] == 5

    asyncio.run(run_test())


def test_setting_driven_date_format(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        svc["setting_service"].get_value.side_effect = lambda key, default=None: {
            "app_date_format": "DD MMM YYYY",
            "default_currency": "BTN",
            "currency_symbol": "Nu.",
        }.get(key, default)

        prop = Property(
            id=11,
            public_id=uuid4(),
            vendor_id=1,
            name="Paro Riverside Eco Stay",
            slug="paro-riverside-eco-stay",
            status=PropertyStatus.ACTIVE,
            price_per_night=4500.0,
            currency="BTN",
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 2,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 3,
            "price_per_night": 4500.0,
            "subtotal": 13500.0,
            "discount_amount": 0.0,
            "tax_amount": 675.0,
            "total_amount": 14175.0,
            "currency": "BTN",
        }

        res = await svc["executor"].execute_tool(
            "check_stay_availability",
            {
                "property_id": "paro-riverside-eco-stay",
                "check_in_date": "2026-10-15",
                "check_out_date": "2026-10-18",
                "num_guests": 2,
            },
        )

        assert res.isError is False
        assert res.data["formatted_check_in_date"] == "15 Oct 2026"
        assert res.data["formatted_check_out_date"] == "18 Oct 2026"
        assert res.data["currency_symbol"] == "Nu."
        assert "Nu." in res.content[0].text
        assert "15 Oct 2026 to 18 Oct 2026" in res.content[0].text

    asyncio.run(run_test())


def test_database_reviews_in_details_and_zero_reviews_rating(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=12,
            public_id=uuid4(),
            vendor_id=1,
            name="New Bumthang Heritage Home",
            slug="new-bumthang-heritage-home",
            status=PropertyStatus.ACTIVE,
            price_per_night=2600.0,
            currency="BTN",
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["review_service"].get_property_rating_summary.return_value = {
            "average_rating": 0.0,
            "total_reviews": 0,
            "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0},
        }
        svc["review_service"].list_by_property.return_value = Page(items=[], total=0, page=1, page_size=5)

        res = await svc["executor"].execute_tool(
            "get_homestay_details",
            {"property_id": "new-bumthang-heritage-home"},
        )

        assert res.isError is False
        assert res.data["rating"] == 0.0
        assert res.data["review_count"] == 0
        assert res.data["recent_reviews"] == []
def test_room_type_capacity_occupancy_pricing_tiers_and_applied_tier(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt = RoomType(
            id=10,
            public_id=uuid4(),
            name="Double Bed",
            capacity=4,
            status=RoomTypeStatus.ACTIVE,
        )
        tier1 = PropertyRoomTypePrice(
            id=1,
            public_id=uuid4(),
            property_room_type_id=101,
            occupancy=2,
            price_per_night=1500.0,
            sale_per_night=0.0,
        )
        tier2 = PropertyRoomTypePrice(
            id=2,
            public_id=uuid4(),
            property_room_type_id=101,
            occupancy=3,
            price_per_night=1550.0,
            sale_per_night=0.0,
        )
        tier3 = PropertyRoomTypePrice(
            id=3,
            public_id=uuid4(),
            property_room_type_id=101,
            occupancy=4,
            price_per_night=1600.0,
            sale_per_night=0.0,
        )
        prt = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=15,
            room_type_id=10,
            room_type=rt,
            price_per_night=1500.0,
            sale_per_night=0.0,
            total_units=5,
            pricing_tiers=[tier1, tier2, tier3],
        )
        prop = Property(
            id=15,
            public_id=uuid4(),
            vendor_id=1,
            name="Beatae Elit Rerum S",
            slug="beatae-elit-rerum-s",
            status=PropertyStatus.ACTIVE,
            price_per_night=1500.0,
            currency="INR",
            property_room_types=[prt],
        )

        svc["prop_service"].get_by_slug.return_value = prop
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 5,
            "room_types_availability": [{"room_type_id": 10, "room_type_name": "Double Bed", "available_units": 5, "is_available": True}],
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 3,
            "price_per_night": 1500.0,
            "subtotal": 4500.0,
            "discount_amount": 0.0,
            "tax_amount": 225.0,
            "total_amount": 4725.0,
            "currency": "INR",
            "applied_tier": {
                "occupancy": 2,
                "price_per_night": 1500.0,
                "sale_per_night": 0.0,
            },
        }

        today = date.today()
        cin = (today + timedelta(days=10)).isoformat()
        cout = (today + timedelta(days=13)).isoformat()

        # 1. Test check_stay_availability returns pricing_tiers and applied_tier
        res = await svc["executor"].execute_tool(
            "check_stay_availability",
            {
                "property_id": "beatae-elit-rerum-s",
                "check_in_date": cin,
                "check_out_date": cout,
                "num_guests": 2,
                "num_rooms": 1,
            },
        )

        assert res.isError is False
        assert res.data["applied_tier"] == {"occupancy": 2, "price_per_night": 1500.0, "sale_per_night": 0.0}
        assert len(res.data["room_types"]) == 1
        rt_res = res.data["room_types"][0]
        assert rt_res["name"] == "Double Bed"
        assert rt_res["capacity"] == 4
        assert len(rt_res["pricing_tiers"]) == 3
        assert rt_res["pricing_tiers"][0]["occupancy"] == 2
        assert rt_res["pricing_tiers"][0]["price_per_night"] == 1500.0
        assert rt_res["pricing_tiers"][1]["occupancy"] == 3
        assert rt_res["pricing_tiers"][1]["price_per_night"] == 1550.0
        assert rt_res["pricing_tiers"][2]["occupancy"] == 4
        assert rt_res["pricing_tiers"][2]["price_per_night"] == 1600.0

        # 2. Test get_homestay_details returns pricing_tiers for room types
        svc["review_service"].get_property_rating_summary.return_value = None
        svc["review_service"].list_by_property.return_value = Page(items=[], total=0, page=1, page_size=5)

        details_res = await svc["executor"].execute_tool(
            "get_homestay_details",
            {"property_id": "beatae-elit-rerum-s"},
        )
        assert details_res.isError is False
        assert len(details_res.data["room_types"]) == 1
        d_rt = details_res.data["room_types"][0]
        assert len(d_rt["pricing_tiers"]) == 3
        assert d_rt["pricing_tiers"][1]["occupancy"] == 3
        assert d_rt["pricing_tiers"][1]["price_per_night"] == 1550.0

    asyncio.run(run_test())


def test_assistant_chat_room_wise_occupancy_rates_presentation(mock_domain_services):
    async def run_test():
        svc = mock_domain_services
        rt = RoomType(
            id=10,
            public_id=uuid4(),
            name="Double Bed",
            capacity=4,
            status=RoomTypeStatus.ACTIVE,
        )
        tier1 = PropertyRoomTypePrice(
            id=1,
            public_id=uuid4(),
            property_room_type_id=101,
            occupancy=2,
            price_per_night=1500.0,
            sale_per_night=0.0,
        )
        tier2 = PropertyRoomTypePrice(
            id=2,
            public_id=uuid4(),
            property_room_type_id=101,
            occupancy=3,
            price_per_night=1550.0,
            sale_per_night=0.0,
        )
        prt = PropertyRoomType(
            id=101,
            public_id=uuid4(),
            property_id=15,
            room_type_id=10,
            room_type=rt,
            price_per_night=1500.0,
            sale_per_night=0.0,
            total_units=5,
            pricing_tiers=[tier1, tier2],
        )
        prop = Property(
            id=15,
            public_id=uuid4(),
            vendor_id=1,
            name="Beatae Elit Rerum S",
            slug="beatae-elit-rerum-s",
            status=PropertyStatus.ACTIVE,
            price_per_night=1500.0,
            currency="INR",
            property_room_types=[prt],
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["review_service"].get_property_rating_summary.return_value = None
        svc["review_service"].list_by_property.return_value = Page(items=[], total=0, page=1, page_size=5)

        assistant = AssistantService(tool_executor=svc["executor"])
        assistant.gemini_key = None
        assistant.openai_key = None

        # Inquire without dates: assistant should list room types and occupancy tiers
        chat_res = await assistant.chat(
            message='What are the room rates for "Beatae Elit Rerum S"?',
            conversation_history=[],
        )
        assert "Double Bed" in chat_res.reply
        assert "Room Rates by Occupancy" in chat_res.reply
        assert "1,500" in chat_res.reply
        assert "1,550" in chat_res.reply

    asyncio.run(run_test())


def test_dynamic_country_and_city_search(mock_domain_services):
    """Test searching with dynamic non-Bhutan country and cities."""
    async def run_test():
        svc = mock_domain_services
        country_nepal = Country(id=10, name="Nepal", code="NP", status=CountryStatus.ACTIVE)
        city_ktm = City(id=101, name="Kathmandu", slug="kathmandu", country_id=10, country=country_nepal, status=CityStatus.ACTIVE)
        city_pkr = City(id=102, name="Pokhara", slug="pokhara", country_id=10, country=country_nepal, status=CityStatus.ACTIVE)

        svc["city_service"].get_all.return_value = [city_ktm, city_pkr]
        svc["country_service"].get_all.return_value = [country_nepal]
        svc["city_service"].get_city_with_is_featured.return_value = [city_ktm, city_pkr]

        prop_ktm = Property(
            id=201,
            public_id=uuid4(),
            vendor_id=1,
            city_id=101,
            name="Kathmandu Peace Homestay",
            slug="kathmandu-peace-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=2500.0,
            currency="NPR",
            type=PropertyType.HOME_STAY,
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop_ktm],
            total=1,
            page=1,
            page_size=10,
        )
        svc["review_service"].get_properties_rating_summary.return_value = {
            201: {"average_rating": 4.8, "total_reviews": 8}
        }

        # Search homestays with dynamic city name
        res = await svc["executor"].execute_tool(
            "search_homestays",
            {"query": "Kathmandu", "guests": 2, "rooms": 1},
        )
        assert res.isError is False
        assert res.data["total"] == 1
        assert res.data["properties"][0]["name"] == "Kathmandu Peace Homestay"
        assert res.data["properties"][0]["currency"] == "NPR"

        # Popular destinations should return active database cities
        dest_res = await svc["executor"].execute_tool("get_popular_destinations", {})
        assert dest_res.isError is False
        assert dest_res.data["country"] == "Nepal"
        dest_names = [d["name"] for d in dest_res.data["destinations"]]
        assert "Kathmandu" in dest_names
        assert "Pokhara" in dest_names

    asyncio.run(run_test())


def test_dynamic_zero_match_fallback_uses_db_cities(mock_domain_services):
    """Test that zero-match assistant responses use dynamic DB cities instead of hardcoded Bhutan/Thimphu."""
    async def run_test():
        svc = mock_domain_services
        country_nepal = Country(id=10, name="Nepal", code="NP", status=CountryStatus.ACTIVE)
        city_ktm = City(id=101, name="Kathmandu", slug="kathmandu", country_id=10, country=country_nepal, status=CityStatus.ACTIVE)
        city_pkr = City(id=102, name="Pokhara", slug="pokhara", country_id=10, country=country_nepal, status=CityStatus.ACTIVE)

        svc["city_service"].get_all.return_value = [city_ktm, city_pkr]
        svc["country_service"].get_all.return_value = [country_nepal]
        svc["city_service"].get_city_with_is_featured.return_value = [city_ktm, city_pkr]
        svc["prop_service"].search_stays.return_value = Page(items=[], total=0, page=1, page_size=10)

        assistant = AssistantService(tool_executor=svc["executor"])

        chat_res = await assistant.chat(
            message="Show me homestays in Atlantis for 2 guests",
            conversation_history=[],
        )
        # Reply must dynamically mention Kathmandu / Pokhara and Nepal, not Bhutan or Thimphu
        assert "Kathmandu" in chat_res.reply or "Pokhara" in chat_res.reply
        assert "Bhutan" not in chat_res.reply
        assert "Thimphu" not in chat_res.reply

    asyncio.run(run_test())


def test_dynamic_mcp_resources_with_db_country(mock_domain_services):
    """Test MCP resources resolve country and cities from database without static Bhutan fallbacks."""
    async def run_test():
        svc = mock_domain_services
        country_nepal = Country(id=10, name="Nepal", code="NP", status=CountryStatus.ACTIVE)
        city_ktm = City(id=101, name="Kathmandu", slug="kathmandu", country_id=10, country=country_nepal, status=CityStatus.ACTIVE)

        svc["city_service"].get_city_with_is_featured.return_value = [city_ktm]
        svc["city_service"].get_all.return_value = [city_ktm]
        svc["country_service"].get_all.return_value = [country_nepal]

        handler = MCPResourceHandler(
            city_service=svc["city_service"],
            country_service=svc["country_service"],
        )

        res_destinations = await handler.read_resource("tashihome://destinations")
        assert len(res_destinations.contents) == 1
        assert "Nepal" in res_destinations.contents[0].text
        assert "Kathmandu" in res_destinations.contents[0].text

        res_featured = await handler.read_resource("tashihome://featured-cities")
        assert len(res_featured.contents) == 1
        assert "Kathmandu" in res_featured.contents[0].text
        assert "Nepal" in res_featured.contents[0].text

    asyncio.run(run_test())


def test_booking_reference_search_flexible_formats(mock_domain_services):
    """Test get_booking_status with various reference formats (with or without hyphen, lowercase, uppercase)."""
    async def run_test():
        svc = mock_domain_services
        booking = Booking(
            id=123,
            public_id=uuid4(),
            booking_reference="BK260908AB12",
            guest_id=10,
            property_id=1,
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            check_in_date=date(2026, 10, 1),
            check_out_date=date(2026, 10, 5),
            num_guests=2,
            num_rooms=1,
            total_amount=12000.0,
            currency="BTN",
        )
        svc["booking_service"].get_by_reference.return_value = booking
        svc["booking_service"].get_booking_by_identifier.return_value = booking

        # 1. Exact reference
        res1 = await svc["executor"].execute_tool("get_booking_status", {"booking_reference": "BK260908AB12"})
        assert res1.isError is False
        assert res1.data["booking_reference"] == "BK260908AB12"
        assert res1.data["status"] == "confirmed"

        # 2. Lowercase reference
        res2 = await svc["executor"].execute_tool("get_booking_status", {"booking_reference": "bk260908ab12"})
        assert res2.isError is False
        assert res2.data["booking_reference"] == "BK260908AB12"

    asyncio.run(run_test())


def test_assistant_chat_booking_reference_search(mock_domain_services):
    """Test AI assistant chat detecting and searching booking reference without strict hyphens."""
    async def run_test():
        svc = mock_domain_services
        booking = Booking(
            id=124,
            public_id=uuid4(),
            booking_reference="BK260908AB12",
            guest_id=10,
            property_id=1,
            status=BookingStatus.CONFIRMED,
            payment_status=PaymentStatus.PAID,
            check_in_date=date(2026, 10, 1),
            check_out_date=date(2026, 10, 5),
            num_guests=2,
            num_rooms=1,
            total_amount=12000.0,
            currency="BTN",
        )
        svc["booking_service"].get_by_reference.return_value = booking
        svc["booking_service"].get_booking_by_identifier.return_value = booking

        assistant = AssistantService(tool_executor=svc["executor"])
        assistant.gemini_key = None
        assistant.openai_key = None
        use_case = ChatAssistantUseCase(assistant_service=assistant)

        # 1. Query with reference code
        req = AssistantChatRequestDTO(message="Where is my reservation BK260908AB12")
        resp = await use_case.execute(req)

        assert resp.intent == "get_booking_status"
        assert len(resp.tool_calls) == 1
        assert resp.tool_calls[0].tool == "get_booking_status"
        assert "BK260908AB12" in resp.reply
        assert "confirmed" in resp.reply.lower()

        # 2. Query with search reference phrase
        req2 = AssistantChatRequestDTO(message="search reference BK260908AB12")
        resp2 = await use_case.execute(req2)
        assert resp2.intent == "get_booking_status"
        assert "BK260908AB12" in resp2.reply

    asyncio.run(run_test())


def test_setting_driven_date_format_in_prompts_and_multi_format_parsing(mock_domain_services):
    """Test setting-driven date format pattern is used in assistant prompt templates and parsed correctly."""
    async def run_test():
        svc = mock_domain_services
        svc["setting_service"].get_value.side_effect = lambda key, default=None: {
            "app_date_format": "DD/MM/YYYY",
            "currency_symbol": "₹",
            "default_currency": "INR",
        }.get(key, default)

        prop = Property(
            id=15,
            public_id=uuid4(),
            vendor_id=1,
            name="Darjeeling Hill View",
            slug="darjeeling-hill-view",
            status=PropertyStatus.ACTIVE,
            price_per_night=2500.0,
            currency="INR",
        )
        svc["prop_service"].get_by_slug.return_value = prop

        assistant = AssistantService(tool_executor=svc["executor"])
        assistant.gemini_key = None
        assistant.openai_key = None

        # 1. Inquire without dates: should prompt with setting-driven date format (DD/MM/YYYY)
        chat_res = await assistant.chat(
            message='What are the rates for "Darjeeling Hill View"?',
            conversation_history=[],
        )
        assert "DD/MM/YYYY" in chat_res.reply

        # 2. Check availability tool with slash date format (DD/MM/YYYY)
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 3,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 4,
            "price_per_night": 2500.0,
            "subtotal": 10000.0,
            "discount_amount": 0.0,
            "tax_amount": 500.0,
            "total_amount": 10500.0,
            "currency": "INR",
        }

        res = await svc["executor"].execute_tool(
            "check_stay_availability",
            {
                "property_id": "darjeeling-hill-view",
                "check_in_date": "10/10/2026",
                "check_out_date": "14/10/2026",
            },
        )
        assert res.isError is False
        assert res.data["is_available"] is True
        assert res.data["formatted_check_in_date"] == "10/10/2026"
        assert res.data["formatted_check_out_date"] == "14/10/2026"

    asyncio.run(run_test())


def test_bedrock_embedding_service_titan_and_batch():
    """Test Amazon Bedrock Titan text embeddings and batch embeddings."""
    async def run_test():
        mock_bedrock = MagicMock()
        fake_emb = [0.123] * 1024
        mock_bedrock.invoke_model.side_effect = lambda **kw: {
            "body": io.BytesIO(json.dumps({"embedding": fake_emb}).encode("utf-8"))
        }

        emb_svc = EmbeddingService(
            provider="bedrock",
            model="amazon.titan-embed-text-v2:0",
            bedrock_region="us-east-1",
            bedrock_access_key_id="test-key",
            bedrock_secret_access_key="test-secret",
        )
        emb_svc._bedrock_client = mock_bedrock

        # 1. Single embedding
        emb = await emb_svc.get_embedding("Luxury cottage in Paro")
        assert len(emb) == 1024
        assert emb[0] == 0.123
        assert mock_bedrock.invoke_model.called

        # 2. Batch embedding
        batch = await emb_svc.get_batch_embeddings(["Cottage 1", "Cottage 2"])
        assert len(batch) == 2
        assert len(batch[0]) == 1024

    asyncio.run(run_test())


def test_bedrock_nova_lite_chat_with_tool_use(mock_domain_services):
    """Test Amazon Bedrock Nova Lite converse chat flow with MCP tool execution."""
    async def run_test():
        svc = mock_domain_services
        mock_bedrock = MagicMock()

        # Turn 1: Bedrock Nova Lite responds with toolUse for search_homestays
        turn1_response = {
            "stopReason": "tool_use",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {
                            "toolUse": {
                                "toolUseId": "tooluse_nova_9988",
                                "name": "search_homestays",
                                "input": {"location_name": "Thimphu"}
                            }
                        }
                    ]
                }
            }
        }

        # Turn 2: After toolResult is passed, Bedrock returns final natural reply
        turn2_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Tashi Delek! I found wonderful homestays in Thimphu for your stay."}
                    ]
                }
            }
        }

        mock_bedrock.converse.side_effect = [turn1_response, turn2_response]

        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="bedrock",
            model="amazon.nova-lite-v1:0",
            bedrock_region="us-east-1",
            bedrock_access_key_id="test-key",
            bedrock_secret_access_key="test-secret",
        )
        assistant._bedrock_client = mock_bedrock

        chat_res = await assistant.chat(
            message="Find me homestays in Thimphu",
            session_id="test-session-nova",
        )

        assert chat_res.intent == "search_homestays"
        assert len(chat_res.tool_calls) == 1
        assert chat_res.tool_calls[0].tool == "search_homestays"
        assert "Thimphu" in chat_res.reply
        assert mock_bedrock.converse.call_count == 2

    asyncio.run(run_test())


def test_bedrock_nova_lite_direct_text_response(mock_domain_services):
    """Test Amazon Bedrock Nova Lite direct greeting/chat without tool calls."""
    async def run_test():
        svc = mock_domain_services
        mock_bedrock = MagicMock()

        greeting_response = {
            "stopReason": "end_turn",
            "output": {
                "message": {
                    "role": "assistant",
                    "content": [
                        {"text": "Tashi Delek! I am Tashi, your AI travel concierge for TashiHome. How can I assist you with your homestay booking today?"}
                    ]
                }
            }
        }
        mock_bedrock.converse.return_value = greeting_response

        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="bedrock",
            model="amazon.nova-lite-v1:0",
            bedrock_region="us-east-1",
        )
        assistant._bedrock_client = mock_bedrock

        chat_res = await assistant.chat(
            message="Hello there!",
            session_id="test-session-greeting",
        )

        assert "Tashi Delek" in chat_res.reply
        assert chat_res.tool_calls == []
        assert mock_bedrock.converse.call_count == 1

    asyncio.run(run_test())


def test_compare_other_homestays_intent_fallback(mock_domain_services):
    """Test that 'Compare other homestays' or 'Compare options' returns comparison list without treating 'Compare Other' as location."""
    async def run_test():
        svc = mock_domain_services
        prop1 = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Heritage Homestay",
            slug="heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=2500.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        prop2 = Property(
            id=2,
            public_id=uuid4(),
            vendor_id=1,
            name="Mountain Bliss",
            slug="mountain-bliss",
            status=PropertyStatus.ACTIVE,
            price_per_night=3500.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop1, prop2],
            total=2,
            page=1,
            page_size=10,
        )

        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="fallback",
        )

        chat_res = await assistant.chat(
            message="Compare other homestays",
            session_id="test-compare-other",
        )

        assert chat_res.reply is not None
        assert "Compare Other" not in chat_res.reply
        assert "0 matching properties" not in chat_res.reply
        assert "Heritage Homestay" in chat_res.reply or "Mountain Bliss" in chat_res.reply
        assert chat_res.search_results is not None
        assert len(chat_res.search_results) == 2
        assert len(chat_res.tool_calls) == 1
        assert chat_res.tool_calls[0].tool == "search_homestays"
        # Tool argument query should NOT be "compare other"
        assert chat_res.tool_calls[0].arguments.get("query") in {"", None}

    asyncio.run(run_test())


def test_mcp_availability_and_details_max_guests_max_rooms_metadata(mock_domain_services):
    """Test that check_stay_availability and get_homestay_details expose max_guests, max_rooms, capacity, total_units."""
    async def run_test():
        svc = mock_domain_services
        rt1 = RoomType(
            id=101,
            public_id=uuid4(),
            name="Deluxe Suite",
            capacity=4,
            status=RoomTypeStatus.ACTIVE,
        )
        tier1 = PropertyRoomTypePrice(
            id=1,
            public_id=uuid4(),
            property_room_type_id=1,
            occupancy=1,
            price_per_night=3500.0,
            sale_per_night=0.0,
        )
        tier2 = PropertyRoomTypePrice(
            id=2,
            public_id=uuid4(),
            property_room_type_id=1,
            occupancy=2,
            price_per_night=4000.0,
            sale_per_night=0.0,
        )
        tier3 = PropertyRoomTypePrice(
            id=3,
            public_id=uuid4(),
            property_room_type_id=1,
            occupancy=4,
            price_per_night=5000.0,
            sale_per_night=0.0,
        )
        prt1 = PropertyRoomType(
            id=1,
            public_id=uuid4(),
            property_id=1,
            room_type_id=101,
            room_type=rt1,
            price_per_night=4000.0,
            sale_per_night=0.0,
            total_units=3,
            pricing_tiers=[tier1, tier2, tier3],
        )
        rt2 = RoomType(
            id=102,
            public_id=uuid4(),
            name="Standard Room",
            capacity=2,
            status=RoomTypeStatus.ACTIVE,
        )
        prt2 = PropertyRoomType(
            id=2,
            public_id=uuid4(),
            property_id=1,
            room_type_id=102,
            room_type=rt2,
            price_per_night=2500.0,
            sale_per_night=0.0,
            total_units=2,
            pricing_tiers=[],
        )
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Beatae elit rerum s",
            slug="beatae-elit-rerum-s",
            status=PropertyStatus.ACTIVE,
            price_per_night=4000.0,
            currency="INR",
            cancellation_policy_id=1,
            property_room_types=[prt1, prt2],
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["prop_service"].get_by_id.return_value = prop
        svc["prop_service"].search_stays.return_value = Page(
            items=[prop],
            total=1,
            page=1,
            page_size=10,
        )
        svc["booking_service"].check_availability.return_value = {
            "is_available": True,
            "available_units": 3,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 1,
            "price_per_night": 4000.0,
            "subtotal": 4000.0,
            "discount_amount": 0.0,
            "tax_amount": 200.0,
            "total_amount": 4200.0,
            "currency": "INR",
        }

        # 1. Test get_homestay_details tool
        details_res = await svc["executor"].execute_tool("get_homestay_details", {"property_id": "beatae-elit-rerum-s"})
        assert not details_res.isError
        assert details_res.data["max_guests"] == 4
        assert details_res.data["max_rooms"] == 5  # sum of rt1 (3) + rt2 (2)
        assert details_res.data["total_units"] == 5
        assert details_res.data["room_types"][0]["capacity"] == 4
        assert details_res.data["room_types"][0]["max_guests"] == 4
        assert details_res.data["room_types"][0]["max_rooms"] == 3

        # 2. Test check_stay_availability tool
        avail_res = await svc["executor"].execute_tool("check_stay_availability", {
            "property_id": "beatae-elit-rerum-s",
            "check_in_date": "2026-10-10",
            "check_out_date": "2026-10-11",
            "num_guests": 2,
            "num_rooms": 1,
        })
        assert not avail_res.isError
        assert avail_res.data["is_available"] is True
        assert avail_res.data["max_rooms"] == 3
        assert avail_res.data["max_guests"] == 12  # 4 capacity * 3 available units
        assert avail_res.data["capacity"] == 4
        assert len(avail_res.data["room_types"]) == 2
        assert avail_res.data["room_types"][0]["capacity"] == 4
        assert avail_res.data["room_types"][0]["max_guests"] == 4
        assert avail_res.data["room_types"][0]["max_rooms"] == 3

        # 3. Test AssistantService full flow for quote query with property name and slug
        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="fallback",
        )
        chat_res = await assistant.chat(
            message='Check availability and price quote for "Beatae elit rerum s" (beatae-elit-rerum-s) from 2026-10-10 to 2026-10-11 for 2 guests.',
            session_id="test-avail-quote",
        )
        assert chat_res.availability is not None
        assert chat_res.availability.get("is_available") is True
        assert chat_res.availability.get("max_guests") == 12
        assert chat_res.availability.get("max_rooms") == 3
        assert len(chat_res.availability.get("room_types")) == 2

    asyncio.run(run_test())


def test_unavailable_homestay_blocks_booking_and_warns_in_chat(mock_domain_services):
    """Test that checking availability for unavailable dates outputs warning and blocks booking creation."""
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=10,
            public_id=uuid4(),
            vendor_id=1,
            name="Grate Hill",
            slug="grate-hill",
            status=PropertyStatus.ACTIVE,
            price_per_night=1000.0,
            currency="INR",
            cancellation_policy_id=1,
        )
        svc["prop_service"].get_by_slug.return_value = prop
        svc["prop_service"].get_by_id.return_value = prop
        # Mock availability as UNAVAILABLE (0 units)
        svc["booking_service"].check_availability.return_value = {
            "is_available": False,
            "available_units": 0,
        }
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 13,
            "price_per_night": 1000.0,
            "subtotal": 13000.0,
            "discount_amount": 0.0,
            "tax_amount": 2340.0,
            "total_amount": 15340.0,
            "currency": "INR",
        }

        # 1. MCP check_stay_availability tool returns is_available: False
        avail_res = await svc["executor"].execute_tool("check_stay_availability", {
            "property_id": "grate-hill",
            "check_in_date": "2026-09-28",
            "check_out_date": "2026-10-11",
            "num_guests": 2,
            "num_rooms": 1,
        })
        assert avail_res.data["is_available"] is False
        assert avail_res.data["available_units"] == 0

        # 2. AssistantService chat for availability quote informs user it is UNAVAILABLE
        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="fallback",
        )
        chat_avail_res = await assistant.chat(
            message='Check availability and quote for Grate Hill from 2026-09-28 to 2026-10-11 for 2 guests.',
            session_id="test-unavail-quote",
        )
        assert "UNAVAILABLE" in chat_avail_res.reply or "unavailable" in chat_avail_res.reply
        assert "Would you like me to book this homestay for you?" not in chat_avail_res.reply
        assert "Book this homestay now" not in chat_avail_res.suggested_actions

        # 3. Direct checkout_and_book attempt throws ROOMS_UNAVAILABLE error and blocks booking
        checkout_res = await svc["executor"].execute_tool("checkout_and_book", {
            "property_id": "grate-hill",
            "check_in_date": "2026-09-28",
            "check_out_date": "2026-10-11",
            "num_guests": 2,
            "num_rooms": 1,
            "guest_name": "Labore error archite",
            "guest_email": "caqefaj@mailinator.com",
            "guest_phone": "+919876543210",
        })
        assert checkout_res.isError is True
        assert checkout_res.data.get("error_code") == "ROOMS_UNAVAILABLE"

        # 4. AssistantService chat for booking blocks the booking creation
        chat_book_res = await assistant.chat(
            message='Book Grate Hill from 2026-09-28 to 2026-10-11 for 2 guests. Name: Labore error archite, Email: caqefaj@mailinator.com, Phone: +919876543210',
            session_id="test-unavail-book",
        )
        assert "Booking Creation Blocked" in chat_book_res.reply or "unavailable" in chat_book_res.reply.lower()
        assert "Reservation Successfully Created" not in chat_book_res.reply
        assert chat_book_res.booking is None

    asyncio.run(run_test())


def test_payment_enabled_config_in_mcp_and_chat(mock_domain_services):
    """Test that PAYMENT_ENABLED=False disables payment links, rejects payment initiation, and shows payment on arrival."""
    async def run_test():
        svc = mock_domain_services
        prop = Property(
            id=1,
            public_id=uuid4(),
            vendor_id=1,
            name="Bhutan Heritage Homestay",
            slug="bhutan-heritage-homestay",
            status=PropertyStatus.ACTIVE,
            price_per_night=3000.0,
            currency="BTN",
            cancellation_policy_id=1,
        )
        user = User(
            id=10,
            public_id=uuid4(),
            full_name="Sonam Dorji",
            email="sonam@test.com",
            phone="+97517112233",
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
        )
        created_booking = Booking(
            id=55,
            public_id=uuid4(),
            booking_reference="BK-2026-PAY-TEST",
            guest_id=10,
            property_id=1,
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            check_in_date=date.today() + timedelta(days=5),
            check_out_date=date.today() + timedelta(days=7),
            num_guests=2,
            num_rooms=1,
            total_amount=6000.0,
            currency="BTN",
        )
        created_booking.guest = user
        created_booking.property = prop

        svc["prop_service"].get_by_slug.return_value = prop
        svc["prop_service"].get_by_id.return_value = prop
        svc["user_service"].get_user_by_email.return_value = user
        svc["user_service"].get_user_by_id.return_value = user
        svc["booking_service"].check_availability.return_value = {"is_available": True, "available_units": 2}
        svc["booking_service"].calculate_pricing_quote.return_value = {
            "num_nights": 2,
            "price_per_night": 3000.0,
            "subtotal": 6000.0,
            "discount_amount": 0.0,
            "tax_amount": 0.0,
            "total_amount": 6000.0,
            "currency": "BTN",
        }
        svc["booking_service"].create_booking.return_value = created_booking
        svc["booking_service"].get_by_reference.return_value = created_booking

        orig_payment_flag = settings.PAYMENT_ENABLED
        try:
            settings.PAYMENT_ENABLED = False

            # 1. MCP initiate_booking_payment tool throws PAYMENT_DISABLED when PAYMENT_ENABLED=False
            pay_res = await svc["executor"].execute_tool("initiate_booking_payment", {"booking_reference": "BK-2026-PAY-TEST"})
            assert pay_res.isError is True
            assert pay_res.data.get("error_code") == "PAYMENT_DISABLED"

            # 2. AssistantService chat payment intent informs user that online payments are disabled
            assistant = AssistantService(
                tool_executor=svc["executor"],
                provider="fallback",
            )
            chat_pay_res = await assistant.chat(
                message="Pay for booking BK-2026-PAY-TEST",
                session_id="test-pay-disabled",
            )
            assert "Online Payments Disabled" in chat_pay_res.reply or "disabled" in chat_pay_res.reply.lower()
            assert "payment_url" not in (chat_pay_res.reply or "")

            # 3. MCP checkout_and_book tool throws PAYMENT_DISABLED when PAYMENT_ENABLED=False
            checkout_res = await svc["executor"].execute_tool("checkout_and_book", {
                "property_id": "bhutan-heritage-homestay",
                "check_in_date": "2026-10-10",
                "check_out_date": "2026-10-12",
                "guest_name": "Sonam Dorji",
                "guest_email": "sonam@test.com",
                "guest_phone": "+97517112233",
            })
            assert checkout_res.isError is True
            assert checkout_res.data.get("error_code") == "PAYMENT_DISABLED"

            # 4. Checkout intent via chat informs user that online booking is disabled
            chat_book_res = await assistant.chat(
                message='Book Bhutan Heritage Homestay from 2026-10-10 to 2026-10-12 for 2 guests. Name: Sonam Dorji, Email: sonam@test.com, Phone: +97517112233',
                session_id="test-checkout-no-pay",
            )
            assert "Booking & Payments Disabled" in chat_book_res.reply or "disabled" in chat_book_res.reply.lower()
            assert chat_book_res.booking is None
            assert "Complete payment online" not in chat_book_res.suggested_actions
            assert "Book this homestay now" not in chat_book_res.suggested_actions

        finally:
            settings.PAYMENT_ENABLED = orig_payment_flag

    asyncio.run(run_test())


def test_setting_driven_currency_and_availability_card_payload(mock_domain_services):
    """Verify that currency code and symbol are setting-driven and availability without dates returns valid card state."""
    async def run_test():
        svc = mock_domain_services
        svc["setting_service"].get_value.side_effect = lambda key: {
            "default_currency": "INR",
            "currency_symbol": "₹",
            "app_date_format": "YYYY-MM-DD",
        }.get(key, None)

        prop_pub_id = uuid4()
        test_prop = Property(
            id=101,
            public_id=prop_pub_id,
            vendor_id=1,
            name="Beatae elit rerum s",
            slug="beatae-elit-rerum-s",
            status=PropertyStatus.ACTIVE,
            price_per_night=1200.0,
            type=PropertyType.HOME_STAY,
            currency=None,  # Not set on property, must fallback to setting_service
        )
        svc["prop_service"].get_all.return_value = Page(items=[test_prop], total=1, page=1, page_size=10)
        svc["prop_service"].search_stays.return_value = Page(items=[test_prop], total=1, page=1, page_size=10)
        svc["prop_service"].get_by_slug = AsyncMock(return_value=test_prop)
        svc["prop_service"].get_by_id = AsyncMock(return_value=test_prop)
        svc["prop_service"].get_by_public_id = AsyncMock(return_value=test_prop)

        assistant = AssistantService(
            tool_executor=svc["executor"],
            provider="fallback",
        )

        # 1. Ask for availability without dates
        res = await assistant.chat(
            message='Check availability and price quote for "Beatae elit rerum s"',
            session_id="test-avail-no-dates",
        )

        assert res.availability is not None
        avail = res.availability
        assert avail.get("currency") == "INR"
        assert avail.get("currency_symbol") == "₹"
        assert avail.get("is_available") is True
        assert avail.get("requires_dates") is True
        assert avail.get("price_per_night") == 1200.0
        assert avail.get("subtotal") == 1200.0
        assert avail.get("total_amount") == 1200.0
        assert "BTN" not in str(avail)

        # 2. Dynamic context verification
        ctx = await assistant._resolve_dynamic_context()
        assert ctx["default_currency"] == "INR"
        assert ctx["currency_symbol"] == "₹"

    asyncio.run(run_test())


def test_assistant_chat_and_dto_validations(mock_domain_services):
    """Test validation constraints on AssistantChatRequestDTO, AssistantCheckoutDTO, AssistantSearchDTO, and AssistantService."""
    from pydantic import ValidationError
    from app.core.exceptions import AppException

    # 1. Empty message validation in AssistantChatRequestDTO
    try:
        AssistantChatRequestDTO(message="   ")
        assert False, "Should raise ValidationError for whitespace-only message"
    except ValidationError:
        pass

    # 2. Invalid phone format in AssistantChatRequestDTO
    try:
        AssistantChatRequestDTO(message="Find homestay", guest_phone="abc-invalid-phone-xyz")
        assert False, "Should raise ValidationError for invalid phone number"
    except ValidationError:
        pass

    # 3. Valid AssistantChatRequestDTO
    dto = AssistantChatRequestDTO(message="  Find homestay in Paro  ", guest_phone="+975-17123456")
    assert dto.message == "Find homestay in Paro"
    assert dto.guest_phone == "+975-17123456"

    # 4. Past check-in date in AssistantCheckoutDTO
    past_date = date.today() - timedelta(days=2)
    future_date = date.today() + timedelta(days=2)
    try:
        AssistantCheckoutDTO(
            property_id="test-prop",
            check_in_date=past_date,
            check_out_date=future_date,
        )
        assert False, "Should raise ValidationError for past check-in date"
    except ValidationError:
        pass

    # 5. Check-out before check-in in AssistantCheckoutDTO
    cin = date.today() + timedelta(days=5)
    cout = date.today() + timedelta(days=3)
    try:
        AssistantCheckoutDTO(
            property_id="test-prop",
            check_in_date=cin,
            check_out_date=cout,
        )
        assert False, "Should raise ValidationError for check-out before check-in"
    except ValidationError:
        pass

    # 6. Stay exceeding 90 days in AssistantCheckoutDTO
    long_cout = cin + timedelta(days=95)
    try:
        AssistantCheckoutDTO(
            property_id="test-prop",
            check_in_date=cin,
            check_out_date=long_cout,
        )
        assert False, "Should raise ValidationError for stay > 90 days"
    except ValidationError:
        pass

    # 7. Search DTO max_price < min_price validation
    try:
        AssistantSearchDTO(min_price=5000, max_price=2000)
        assert False, "Should raise ValidationError for max_price < min_price"
    except ValidationError:
        pass

    # 8. AssistantService.chat empty message rejection
    async def test_service_chat_empty():
        svc = mock_domain_services
        assistant = AssistantService(tool_executor=svc["executor"], provider="fallback")
        try:
            await assistant.chat(message="   ")
            assert False, "Should raise AppException for empty message"
        except AppException as e:
            assert e.status_code == 400
            assert e.error_code == "EMPTY_MESSAGE"

    asyncio.run(test_service_chat_empty())













