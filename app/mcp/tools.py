import inspect
import json
import logging
import re
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import PasswordHasher
from app.events.events.users.create_user_event import CreateUserEvent
from app.models.booking_model import Booking, BookingStatus, PaymentStatus
from app.models.payment_model import Payment, PaymentMethod, TransactionStatus
from app.models.property_model import PropertyStatus
from app.models.user_model import User, UserRole, UserStatus
from app.mcp.protocol import CallToolResult, TextContent, Tool

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------------------
# Tool Definitions (Schemas)
# ------------------------------------------------------------------------------

SEARCH_HOMESTAYS_TOOL = Tool(
    name="search_homestays",
    description="Search for homestays and rooms by location/neighborhood, street address, city, dates, guests count, budget, property type, and amenities.",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "General search query, destination, city, neighborhood, or landmark.",
            },
            "location_name": {
                "type": "string",
                "description": "Specific location, neighborhood, or landmark area.",
            },
            "address": {
                "type": "string",
                "description": "Street address or road name.",
            },
            "city_name": {
                "type": "string",
                "description": "Specific city name filter.",
            },
            "check_in_date": {
                "type": "string",
                "format": "date",
                "description": "Check-in date in YYYY-MM-DD format.",
            },
            "check_out_date": {
                "type": "string",
                "format": "date",
                "description": "Check-out date in YYYY-MM-DD format.",
            },
            "guests": {
                "type": "integer",
                "description": "Total number of guests (adults + children). Default is 1.",
            },
            "rooms": {
                "type": "integer",
                "description": "Number of rooms required. Default is 1.",
            },
            "min_price": {
                "type": "number",
                "description": "Minimum price per night in local currency (e.g. INR / USD / BTN).",
            },
            "max_price": {
                "type": "number",
                "description": "Maximum price per night in local currency (e.g. INR / USD / BTN).",
            },
            "property_type": {
                "type": "string",
                "description": "Property type: 'ENTIRE_PLACE', 'PRIVATE_ROOM', 'SHARED_ROOM', 'HOMESTAY', etc.",
            },
            "amenity_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of amenity IDs required (e.g. WiFi, Heating, Hot Water).",
            },
            "facility_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of facility IDs required (e.g. Parking, Restaurant, Garden).",
            },
            "page": {
                "type": "integer",
                "description": "Page number (default 1).",
            },
            "page_size": {
                "type": "integer",
                "description": "Number of homestays to return (default 10, max 30).",
            },
        },
    },
)

CHECK_AVAILABILITY_TOOL = Tool(
    name="check_stay_availability",
    description="Check room availability and calculate a detailed pricing quote (nightly rates, taxes, discounts, total) for a homestay. Note: check_in_date and check_out_date must be provided by the user in YYYY-MM-DD format (must be current or future dates). If the user has not provided check-in and check-out dates, ask the user for their desired dates before calling this tool.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {
                "type": "string",
                "description": "The property identifier: slug (e.g. 'bhutan-peaceful-homestay'), public UUID, or database ID.",
            },
            "check_in_date": {
                "type": "string",
                "format": "date",
                "description": "Check-in date in YYYY-MM-DD format.",
            },
            "check_out_date": {
                "type": "string",
                "format": "date",
                "description": "Check-out date in YYYY-MM-DD format.",
            },
            "num_guests": {
                "type": "integer",
                "description": "Number of guests staying. Default is 1.",
            },
            "num_rooms": {
                "type": "integer",
                "description": "Number of rooms needed. Default is 1.",
            },
            "room_type_id": {
                "type": "string",
                "description": "Optional specific room type ID or public UUID.",
            },
        },
        "required": ["property_id", "check_in_date", "check_out_date"],
    },
)

GET_HOMESTAY_DETAILS_TOOL = Tool(
    name="get_homestay_details",
    description="Retrieve comprehensive details about a specific homestay including available room types, amenities, facilities, food options, check-in/out policies, and host information.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {
                "type": "string",
                "description": "The homestay slug, public UUID, or database ID.",
            },
        },
        "required": ["property_id"],
    },
)

REGISTER_GUEST_USER_TOOL = Tool(
    name="register_guest_user",
    description="Register a new guest user account in TashiHome so they can proceed with bookings, manage reservations, and receive notifications.",
    inputSchema={
        "type": "object",
        "properties": {
            "full_name": {
                "type": "string",
                "description": "Full legal name of the guest.",
            },
            "email": {
                "type": "string",
                "format": "email",
                "description": "Valid email address for confirmations and account management.",
            },
            "phone": {
                "type": "string",
                "description": "Mobile / phone number with country code.",
            },
            "password": {
                "type": "string",
                "description": "Optional password (if not provided, an initial temporary password will be generated).",
            },
            "is_subscribed": {
                "type": "boolean",
                "description": "Whether to subscribe to travel updates and newsletters.",
            },
        },
        "required": ["full_name", "email", "phone"],
    },
)

CHECKOUT_AND_BOOK_TOOL = Tool(
    name="checkout_and_book",
    description="Complete checkout and create a homestay reservation. If the guest is not registered or not logged in, this tool automatically verifies/registers their account and books the stay.",
    inputSchema={
        "type": "object",
        "properties": {
            "property_id": {
                "type": "string",
                "description": "The homestay slug, public UUID, or database ID to book.",
            },
            "check_in_date": {
                "type": "string",
                "format": "date",
                "description": "Check-in date in YYYY-MM-DD format.",
            },
            "check_out_date": {
                "type": "string",
                "format": "date",
                "description": "Check-out date in YYYY-MM-DD format.",
            },
            "num_guests": {
                "type": "integer",
                "description": "Number of guests (default 1).",
            },
            "num_rooms": {
                "type": "integer",
                "description": "Number of rooms to reserve (default 1).",
            },
            "room_type_id": {
                "type": "string",
                "description": "Optional specific room type ID or UUID.",
            },
            "special_requests": {
                "type": "string",
                "description": "Special requests for the host (e.g. late check-in, vegetarian meals, airport pickup).",
            },
            "guest_name": {
                "type": "string",
                "description": "Guest's full name (required if user is unauthenticated or registering).",
            },
            "guest_email": {
                "type": "string",
                "format": "email",
                "description": "Guest's email address (required if user is unauthenticated or registering).",
            },
            "guest_phone": {
                "type": "string",
                "description": "Guest's phone number with country code (required if registering).",
            },
            "guest_password": {
                "type": "string",
                "description": "Optional password for creating the account if new.",
            },
        },
        "required": ["property_id", "check_in_date", "check_out_date"],
    },
)

GET_BOOKING_STATUS_TOOL = Tool(
    name="get_booking_status",
    description="Lookup the status, dates, guest details, homestay info, and payment condition of an existing booking using the booking reference or ID.",
    inputSchema={
        "type": "object",
        "properties": {
            "booking_reference": {
                "type": "string",
                "description": "The unique booking reference code (e.g., 'BK-20260908-ABCD') or booking ID.",
            },
        },
        "required": ["booking_reference"],
    },
)

CANCEL_BOOKING_TOOL = Tool(
    name="cancel_booking",
    description="Request cancellation of a booking reservation with a specified reason.",
    inputSchema={
        "type": "object",
        "properties": {
            "booking_reference": {
                "type": "string",
                "description": "The unique booking reference code or booking ID.",
            },
            "reason": {
                "type": "string",
                "description": "Reason for cancellation.",
            },
        },
        "required": ["booking_reference"],
    },
)

GET_POPULAR_DESTINATIONS_TOOL = Tool(
    name="get_popular_destinations",
    description="Get popular travel destinations, cities, and locations with available homestay counts directly from database.",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "Maximum number of destinations to return (default 6).",
            },
        },
    },
)

SEMANTIC_SEARCH_HOMESTAYS_TOOL = Tool(
    name="semantic_search_homestays",
    description="Perform AI vector semantic search for homestays based on vibe, atmosphere, natural language descriptions, scenic views, amenities, or specific traveler preferences (e.g. 'cozy wooden cottage with fireplace and mountain view', 'peaceful retreat for meditation near apple orchard').",
    inputSchema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Descriptive, atmospheric, or vibe-based search query.",
            },
            "city_name": {
                "type": "string",
                "description": "Optional city/district filter.",
            },
            "min_price": {
                "type": "number",
                "description": "Optional minimum nightly price.",
            },
            "max_price": {
                "type": "number",
                "description": "Optional maximum nightly price.",
            },
            "property_type": {
                "type": "string",
                "description": "Optional property type filter.",
            },
            "limit": {
                "type": "integer",
                "description": "Maximum number of homestays to return (default 8).",
            },
            "min_similarity": {
                "type": "number",
                "description": "Minimum similarity score threshold (0.0 - 1.0, default 0.25).",
            },
        },
        "required": ["query"],
    },
)

INITIATE_BOOKING_PAYMENT_TOOL = Tool(
    name="initiate_booking_payment",
    description="Generate or retrieve payment gateway checkout details (e.g. Razorpay Order ID, Key ID, payment URL, and remaining balance) for an existing reservation so the guest can complete their payment.",
    inputSchema={
        "type": "object",
        "properties": {
            "booking_reference": {
                "type": "string",
                "description": "The unique booking reference code (e.g., 'BK-20260908-ABCD') or booking UUID.",
            },
            "amount": {
                "type": "number",
                "description": "Optional specific amount to pay. If omitted, the entire remaining balance is used.",
            },
            "payment_method": {
                "type": "string",
                "description": "Preferred payment method: 'card', 'upi', 'netbanking', 'wallet', 'bank_transfer'. Default is 'card'.",
            },
        },
        "required": ["booking_reference"],
    },
)

ALL_MCP_TOOLS: List[Tool] = [
    SEARCH_HOMESTAYS_TOOL,
    SEMANTIC_SEARCH_HOMESTAYS_TOOL,
    CHECK_AVAILABILITY_TOOL,
    GET_HOMESTAY_DETAILS_TOOL,
    REGISTER_GUEST_USER_TOOL,
    CHECKOUT_AND_BOOK_TOOL,
    INITIATE_BOOKING_PAYMENT_TOOL,
    GET_BOOKING_STATUS_TOOL,
    CANCEL_BOOKING_TOOL,
    GET_POPULAR_DESTINATIONS_TOOL,
]


# ------------------------------------------------------------------------------
# Tool Handlers Execution Registry
# ------------------------------------------------------------------------------

class MCPToolExecutor:
    """Executes MCP tools against TashiHome domain services."""

    def __init__(
        self,
        property_service: Any,
        booking_service: Any,
        user_service: Any,
        payment_service: Optional[Any] = None,
        razorpay_service: Optional[Any] = None,
        city_service: Optional[Any] = None,
        location_service: Optional[Any] = None,
        country_service: Optional[Any] = None,
        room_type_service: Optional[Any] = None,
        property_room_type_service: Optional[Any] = None,
        tax_service: Optional[Any] = None,
        setting_service: Optional[Any] = None,
        review_service: Optional[Any] = None,
        vector_search_service: Optional[Any] = None,
        event_bus: Optional[Any] = None,
    ):
        self.property_service = property_service
        self.booking_service = booking_service
        self.user_service = user_service
        self.payment_service = payment_service
        self.razorpay_service = razorpay_service
        self.city_service = city_service
        self.location_service = location_service
        self.country_service = country_service
        self.room_type_service = room_type_service
        self.property_room_type_service = property_room_type_service
        self.tax_service = tax_service
        self.setting_service = setting_service
        self.review_service = review_service
        self.vector_search_service = vector_search_service
        self.event_bus = event_bus
        self.password_hasher = PasswordHasher()

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> CallToolResult:
        """Route tool invocation to the corresponding async handler."""
        try:
            if tool_name == "search_homestays":
                return await self._handle_search_homestays(arguments)
            elif tool_name == "semantic_search_homestays":
                return await self._handle_semantic_search_homestays(arguments)
            elif tool_name == "check_stay_availability":
                return await self._handle_check_availability(arguments)
            elif tool_name == "get_homestay_details":
                return await self._handle_get_homestay_details(arguments)
            elif tool_name == "register_guest_user":
                return await self._handle_register_guest_user(arguments)
            elif tool_name == "checkout_and_book":
                return await self._handle_checkout_and_book(arguments, current_user_id)
            elif tool_name == "initiate_booking_payment":
                return await self._handle_initiate_booking_payment(arguments, current_user_id)
            elif tool_name == "get_booking_status":
                return await self._handle_get_booking_status(arguments, current_user_id)
            elif tool_name == "cancel_booking":
                return await self._handle_cancel_booking(arguments, current_user_id)
            elif tool_name == "get_popular_destinations":
                return await self._handle_get_popular_destinations(arguments)
            else:
                return CallToolResult(
                    content=[TextContent(text=f"Unknown tool: '{tool_name}'")],
                    isError=True,
                )
        except AppException as e:
            detail = getattr(e, "detail", {})
            err_code = getattr(e, "error_code", None) or (detail.get("error_code") if isinstance(detail, dict) else None)
            field = getattr(e, "field", None) or (detail.get("field") if isinstance(detail, dict) else None)
            msg = getattr(e, "message", None) or (detail.get("message") if isinstance(detail, dict) else str(e))
            return CallToolResult(
                content=[TextContent(text=f"Error: {msg}")],
                isError=True,
                data={"error_code": err_code, "status_code": getattr(e, "status_code", 400), "field": field},
            )
        except Exception as e:
            logger.exception("Error executing MCP tool '%s': %s", tool_name, e)
            return CallToolResult(
                content=[TextContent(text=f"Unexpected error executing {tool_name}: {str(e)}")],
                isError=True,
            )

    # --------------------------------------------------------------------------
    # Handlers Implementation & Setting Helpers
    # --------------------------------------------------------------------------

    CURRENCY_SYMBOL_MAP: Dict[str, str] = {
        "BTN": "Nu.",
        "INR": "₹",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "NPR": "रू",
        "THB": "฿",
    }

    async def _resolve_currency_and_symbol(self, property_currency: Optional[str] = None) -> tuple[str, str]:
        """Returns (currency_code, currency_symbol) resolved dynamically from SettingService or property defaults."""
        setting_curr = None
        setting_sym = None
        if self.setting_service:
            try:
                setting_curr = await self.setting_service.get_value("default_currency")
                setting_sym = await self.setting_service.get_value("currency_symbol")
            except Exception:
                pass

        currency_code = property_currency.strip().upper() if isinstance(property_currency, str) and property_currency.strip() else None
        if not currency_code:
            currency_code = setting_curr.strip().upper() if setting_curr and isinstance(setting_curr, str) and setting_curr.strip() else "INR"

        symbol = setting_sym.strip() if setting_sym and isinstance(setting_sym, str) and setting_sym.strip() else None
        if not symbol:
            symbol = self.CURRENCY_SYMBOL_MAP.get(currency_code, "₹" if currency_code in {"INR", "BTN"} else currency_code)

        return str(currency_code), str(symbol)

    async def _get_date_format_pattern(self) -> str:
        """Returns the setting-driven date format pattern (e.g., 'YYYY-MM-DD', 'DD/MM/YYYY', 'DD MMM YYYY')."""
        if self.setting_service:
            try:
                fmt = await self.setting_service.get_value("app_date_format") or await self.setting_service.get_value("date_format")
                if fmt and isinstance(fmt, str):
                    return fmt.strip()
            except Exception:
                pass
        return "YYYY-MM-DD"

    def _format_date_with_pattern(self, d: Optional[date | datetime | str], pattern: str = "YYYY-MM-DD") -> str:
        """Converts a date object/string to the specified formatted string based on setting pattern."""
        if not d:
            return ""
        parsed_date: Optional[date] = None
        if isinstance(d, datetime):
            parsed_date = d.date()
        elif isinstance(d, date):
            parsed_date = d
        elif isinstance(d, str):
            parsed_date = self._parse_date(d)

        if not parsed_date:
            return str(d)

        pat_upper = (pattern or "YYYY-MM-DD").strip().upper()
        if pat_upper in {"DD/MM/YYYY", "D/M/YYYY"}:
            return parsed_date.strftime("%d/%m/%Y")
        elif pat_upper in {"DD-MM-YYYY", "D-M-YYYY"}:
            return parsed_date.strftime("%d-%m-%Y")
        elif pat_upper in {"MM/DD/YYYY", "M/D/YYYY"}:
            return parsed_date.strftime("%m/%d/%Y")
        elif "MMM" in pat_upper:
            if "DD" in pat_upper and "," in pat_upper:
                return parsed_date.strftime("%b %d, %Y")
            elif "DD" in pat_upper:
                return parsed_date.strftime("%d %b %Y")
            else:
                return parsed_date.strftime("%b %d, %Y")
        elif pat_upper in {"YYYY/MM/DD"}:
            return parsed_date.strftime("%Y/%m/%d")
        elif pat_upper in {"YYYY-MM-DD"}:
            return parsed_date.strftime("%Y-%m-%d")
        else:
            return parsed_date.strftime("%Y-%m-%d")

    async def _format_date(self, d: Optional[date | datetime | str]) -> str:
        pattern = await self._get_date_format_pattern()
        return self._format_date_with_pattern(d, pattern)

    def _parse_date(self, val: Any) -> Optional[date]:
        if not val:
            return None
        if isinstance(val, date):
            return val
        if isinstance(val, str):
            val_str = val.strip()
            # Try multiple common date formats
            for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%m/%d/%Y", "%Y/%m/%d", "%d %b %Y", "%b %d, %Y", "%d %B %Y", "%B %d, %Y"]:
                try:
                    return datetime.strptime(val_str, fmt).date()
                except ValueError:
                    continue
        return None

    async def _find_booking(self, ref: str, with_relations: Optional[Dict[str, bool]] = None) -> Optional[Booking]:
        """Robust multi-strategy lookup for bookings by reference, UUID, or ID."""
        if not self.booking_service or not ref:
            return None
        clean_ref = str(ref).strip()
        booking = None

        async def _call(fn_name: str, arg: Any):
            fn = getattr(self.booking_service, fn_name, None)
            if fn and callable(fn):
                try:
                    res = fn(arg, with_relations=with_relations)
                    if inspect.isawaitable(res):
                        return await res
                    return res
                except Exception:
                    return None
            return None

        # 1. Try by reference / identifier directly
        booking = await _call("get_by_reference", clean_ref)
        if not booking:
            booking = await _call("get_booking_by_identifier", clean_ref)

        # 2. Try uppercase if different
        if not booking and clean_ref.upper() != clean_ref:
            booking = await _call("get_by_reference", clean_ref.upper())
            if not booking:
                booking = await _call("get_booking_by_identifier", clean_ref.upper())

        # 3. Try UUID
        if not booking:
            try:
                uuid_obj = UUID(clean_ref)
                booking = await _call("get_by_public_id", str(uuid_obj))
            except (ValueError, AttributeError):
                pass

        # 4. Try integer ID
        if not booking and clean_ref.isdigit():
            booking = await _call("get_by_id", int(clean_ref))

        return booking

    async def _resolve_platform_country(self) -> Optional[str]:
        """Resolve active platform country from settings or country service."""
        if self.setting_service:
            try:
                val = await self.setting_service.get_value("country") or await self.setting_service.get_value("default_country")
                if val and isinstance(val, str):
                    return val.strip()
            except Exception:
                pass
        if self.country_service:
            try:
                countries = await self.country_service.get_all()
                items = getattr(countries, "items", countries) or []
                if items:
                    c_name = getattr(items[0], "name", None)
                    if c_name and isinstance(c_name, str):
                        return c_name
            except Exception:
                pass
        return None

    async def _get_active_cities_map(self) -> Dict[str, str]:
        """Retrieve active cities mapping {lowercase_name: display_name, lowercase_slug: display_name} from database."""
        cities_map: Dict[str, str] = {}
        if self.city_service:
            try:
                res = await self.city_service.get_all()
                items = getattr(res, "items", res) or []
                for c in items:
                    c_name = getattr(c, "name", None)
                    c_slug = getattr(c, "slug", None)
                    if c_name and isinstance(c_name, str):
                        cities_map[c_name.lower().strip()] = c_name
                    if c_slug and isinstance(c_slug, str):
                        cities_map[c_slug.lower().strip()] = c_name if (c_name and isinstance(c_name, str)) else c_slug
            except Exception as e:
                logger.warning("Could not fetch active cities from DB: %s", e)
        return cities_map

    async def _get_active_locations_map(self) -> Dict[str, str]:
        """Retrieve active locations mapping {lowercase_name: display_name, lowercase_slug: display_name} from database."""
        locations_map: Dict[str, str] = {}
        if self.location_service:
            try:
                res = await self.location_service.list(page=1, page_size=100)
                items = getattr(res, "items", res) or []
                for loc in items:
                    l_name = getattr(loc, "name", None)
                    l_slug = getattr(loc, "slug", None)
                    if l_name and isinstance(l_name, str):
                        locations_map[l_name.lower().strip()] = l_name
                    if l_slug and isinstance(l_slug, str):
                        locations_map[l_slug.lower().strip()] = l_name if (l_name and isinstance(l_name, str)) else l_slug
            except Exception as e:
                logger.warning("Could not fetch active locations from DB: %s", e)
        return locations_map

    async def _resolve_property(self, property_id: str) -> Any:
        prop_str = str(property_id).strip()
        prop = None
        try:
            uuid_obj = UUID(prop_str)
            prop = await self.property_service.get_by_public_id(
                str(uuid_obj),
                with_relations={
                    "city": True,
                    "location": True,
                    "cancellation_policy": True,
                    "property_room_types": True,
                    "property_amenities": True,
                    "property_facilities": True,
                    "property_food_options": True,
                    "property_assets": True,
                },
            )
        except (ValueError, AttributeError):
            if prop_str.isdigit():
                prop = await self.property_service.get_by_id(
                    int(prop_str),
                    with_relations={
                        "city": True,
                        "location": True,
                        "cancellation_policy": True,
                        "property_room_types": True,
                        "property_amenities": True,
                        "property_facilities": True,
                        "property_food_options": True,
                        "property_assets": True,
                    },
                )
            else:
                prop = await self.property_service.get_by_slug(
                    prop_str,
                    with_relations={
                        "city": True,
                        "location": True,
                        "cancellation_policy": True,
                        "property_room_types": True,
                        "property_amenities": True,
                        "property_facilities": True,
                        "property_food_options": True,
                        "property_assets": True,
                    },
                )
                if not prop:
                    normalized_slug = re.sub(r"[^a-zA-Z0-9]+", "-", prop_str).strip("-").lower()
                    if normalized_slug and normalized_slug != prop_str:
                        prop = await self.property_service.get_by_slug(
                            normalized_slug,
                            with_relations={
                                "city": True,
                                "location": True,
                                "cancellation_policy": True,
                                "property_room_types": True,
                                "property_amenities": True,
                                "property_facilities": True,
                                "property_food_options": True,
                                "property_assets": True,
                            },
                        )
                if not prop:
                    # Fallback: search by property title/name
                    clean_name = re.sub(r'["\']', '', prop_str).strip()
                    try:
                        search_res = await self.property_service.search_stays(
                            region=clean_name,
                            page=1,
                            page_size=1,
                            with_relations={
                                "city": True,
                                "location": True,
                                "cancellation_policy": True,
                                "property_room_types": True,
                                "property_amenities": True,
                                "property_facilities": True,
                                "property_food_options": True,
                                "property_assets": True,
                            },
                        )
                        items = getattr(search_res, "items", search_res) or []
                        if items:
                            prop = items[0]
                    except Exception as e:
                        logger.warning("Could not resolve property via search_stays: %s", e)
        return prop

    async def _resolve_room_type(self, prop: Any, room_type_arg: Any) -> Optional[int]:
        """Resolves room type integer ID from UUID, integer string, or room type name/slug."""
        if not prop:
            return None
        if not room_type_arg:
            if hasattr(prop, "property_room_types") and prop.property_room_types and len(prop.property_room_types) == 1:
                return prop.property_room_types[0].room_type_id
            return None

        arg_str = str(room_type_arg).strip()

        # 1. Try match by UUID
        try:
            rt_uuid = UUID(arg_str)
            if hasattr(prop, "property_room_types") and prop.property_room_types:
                for prt in prop.property_room_types:
                    if str(getattr(prt, "public_id", "")) == str(rt_uuid) or (hasattr(prt, "room_type") and prt.room_type and str(getattr(prt.room_type, "public_id", "")) == str(rt_uuid)):
                        return prt.room_type_id
            if self.room_type_service:
                rt = await self.room_type_service.get_by_public_id(str(rt_uuid))
                if rt and getattr(rt, "id", None) and isinstance(rt.id, int):
                    return rt.id
        except (ValueError, AttributeError):
            pass

        # 2. Try integer ID
        if arg_str.isdigit():
            val = int(arg_str)
            if hasattr(prop, "property_room_types") and prop.property_room_types:
                for prt in prop.property_room_types:
                    if prt.room_type_id == val or getattr(prt, "id", None) == val:
                        return prt.room_type_id
            return val

        # 3. Match by name or slug within property's room types
        if hasattr(prop, "property_room_types") and prop.property_room_types:
            for prt in prop.property_room_types:
                rt = getattr(prt, "room_type", None)
                if rt:
                    rt_name = getattr(rt, "name", "").lower()
                    rt_slug = getattr(rt, "slug", "").lower()
                    if arg_str.lower() in rt_name or rt_name in arg_str.lower() or arg_str.lower() == rt_slug:
                        return prt.room_type_id

        # 4. Fallback: search room_type_service
        if self.room_type_service:
            try:
                rt = await self.room_type_service.get_by_slug(arg_str.lower().replace(" ", "-"))
                if rt:
                    return rt.id
            except Exception:
                pass

        return None

    async def _resolve_tax_settings(self) -> tuple[float, bool, Optional[str], Optional[str]]:
        if self.tax_service:
            try:
                default_tax = await self.tax_service.get_default_tax()
                if default_tax and default_tax.rate is not None:
                    return (
                        float(default_tax.rate),
                        bool(default_tax.is_inclusive),
                        default_tax.name,
                        default_tax.code,
                    )
            except Exception:
                pass
        if self.setting_service:
            try:
                is_gst_enabled = await self.setting_service.get_value("is_gst_enabled", "false")
                if is_gst_enabled and is_gst_enabled.lower() == "true":
                    gst_pct = await self.setting_service.get_value("gst_percentage", "0")
                    is_inc = await self.setting_service.get_value("is_tax_inclusive", "false")
                    return float(gst_pct or 0), is_inc.lower() == "true", "GST", "GST"
            except Exception:
                pass
        return 0.0, False, None, None

    async def _handle_search_homestays(self, args: Dict[str, Any]) -> CallToolResult:
        raw_query = (args.get("query") or "").strip()
        city_name = args.get("city_name")
        location_name = args.get("location_name")
        address = args.get("address")
        check_in = self._parse_date(args.get("check_in_date"))
        check_out = self._parse_date(args.get("check_out_date"))
        guests = args.get("guests")
        rooms = args.get("rooms", 1) or 1
        min_price = args.get("min_price")
        max_price = args.get("max_price")
        prop_type = args.get("property_type")
        page = int(args.get("page", 1) or 1)
        page_size = min(int(args.get("page_size", args.get("limit", 10)) or 10), 50)

        # Resolve active cities, locations, and country dynamically
        active_cities = await self._get_active_cities_map()
        active_locations = await self._get_active_locations_map()
        platform_country = (await self._resolve_platform_country() or "").lower()

        # Extract address from query if specified as "address Norzin Lam" or "at Norzin Lam" and not explicitly passed
        if not address and raw_query:
            addr_m = re.search(r"(?:address[:\s]+|at\s+address[:\s]+|street[:\s]+|road[:\s]+)([\w\s,.-]+?)(?:\s+in|\s+near|\s+from|\s+for|\s+page|$)", raw_query, flags=re.IGNORECASE)
            if addr_m:
                address = addr_m.group(1).strip()
                raw_query = raw_query.replace(addr_m.group(0), " ").strip()

        # Extract location/neighborhood if specified as "near Motithang" and not explicitly passed
        if not location_name and raw_query:
            loc_m = re.search(r"(?:near|location|area|neighborhood)\s+([\w\s-]+?)(?:\s+at|\s+address|\s+from|\s+in|\s+for|\s+with|\s+page|$)", raw_query, flags=re.IGNORECASE)
            if loc_m:
                candidate_loc = loc_m.group(1).strip()
                if candidate_loc.lower() not in active_cities:
                    location_name = candidate_loc
                    raw_query = raw_query.replace(loc_m.group(0), " ").strip()

        # Extract page number if present in query e.g. "page 2"
        if "page" not in args and raw_query:
            pg_m = re.search(r"\bpage\s*(\d+)\b", raw_query, flags=re.IGNORECASE)
            if pg_m:
                page = int(pg_m.group(1))
                raw_query = re.sub(r"\bpage\s*\d+\b", "", raw_query, flags=re.IGNORECASE).strip()

        # Normalize query and strip intent/filler noise words
        noise_pattern = r"\b(find|search|show|get|look\s+for|explore|compare|comparison|other|another|different|various|options?|alternatives?|similar|view|browse|list|all|available|homestays?|homstays?|homestay|homstay|propert(?:y|ies)|stays?|rooms?|hotels?|accommodations?|place|places|in|at|near|around|for|please|me|best|top|good|check)\b"
        cleaned_query = re.sub(noise_pattern, "", raw_query, flags=re.IGNORECASE).strip()
        cleaned_query = re.sub(r"\s+", " ", cleaned_query).strip()

        region = None
        q_lower = cleaned_query.lower()

        # Check if query matches a known dynamic city
        matched_city = None
        for key, val in active_cities.items():
            if key in q_lower:
                matched_city = val
                break

        # Check if query matches a known dynamic location
        matched_location = None
        if not location_name and not matched_city:
            for key, val in active_locations.items():
                if key in q_lower:
                    matched_location = val
                    break

        if matched_city:
            if not city_name:
                city_name = matched_city
            rem = re.sub(rf"\b{matched_city.lower()}\b", "", q_lower, flags=re.IGNORECASE).strip()
            region = rem if rem else None
        elif matched_location:
            if not location_name:
                location_name = matched_location
            rem = re.sub(rf"\b{matched_location.lower()}\b", "", q_lower, flags=re.IGNORECASE).strip()
            region = rem if rem else None
        elif platform_country and platform_country in q_lower:
            rem = re.sub(rf"\b{platform_country}\b", "", q_lower, flags=re.IGNORECASE).strip()
            region = rem if rem else None
        elif q_lower in {"all", "any", "everywhere", "compare", "other", "compare other", "options", "another", "different"}:
            region = None
        else:
            region = cleaned_query if cleaned_query else None

        page_result = await self.property_service.search_stays(
            region=region,
            address=address,
            city_name=city_name,
            location_name=location_name,
            check_in_date=check_in,
            check_out_date=check_out,
            guests=guests,
            rooms=rooms,
            min_price=min_price,
            max_price=max_price,
            property_type=prop_type,
            page=page,
            page_size=page_size,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
                "property_room_types": True,
            },
            flush=True,
        )

        rating_summaries = {}
        if self.review_service and page_result.items:
            prop_ids = [p.id for p in page_result.items if p.id]
            rating_summaries = await self.review_service.get_properties_rating_summary(prop_ids)

        items_data = []
        for prop in page_result.items:
            rating_info = rating_summaries.get(prop.id) if isinstance(rating_summaries, dict) else None
            avg_rating = 0.0
            review_count = 0
            if isinstance(rating_info, dict):
                avg_rating = float(rating_info.get("average_rating") or rating_info.get("avg_rating") or 0.0)
                review_count = int(rating_info.get("total_reviews") or rating_info.get("reviews_count") or 0)
            elif isinstance(rating_info, (int, float)):
                avg_rating = float(rating_info)

            cover_image = None
            if hasattr(prop, "property_assets") and prop.property_assets:
                cover_image = prop.property_assets[0].url if hasattr(prop.property_assets[0], "url") else None

            city_title = prop.city.name if getattr(prop, "city", None) and hasattr(prop.city, "name") else None
            loc_title = prop.location.name if getattr(prop, "location", None) and hasattr(prop.location, "name") else None

            raw_price = getattr(prop, "sale_per_night", None) or getattr(prop, "price_per_night", None) or getattr(prop, "base_price", None)
            base_price = float(raw_price) if raw_price is not None else 0.0

            prop_type_val = getattr(prop, "type", None) or getattr(prop, "property_type", "homestay")
            prop_type_str = str(getattr(prop_type_val, "value", prop_type_val))

            curr_code, curr_sym = await self._resolve_currency_and_symbol(getattr(prop, "currency", None))

            items_data.append({
                "id": str(getattr(prop, "public_id", prop.id)),
                "name": prop.name,
                "slug": prop.slug,
                "city": city_title,
                "location": loc_title,
                "address": getattr(prop, "address", None),
                "base_price": base_price,
                "currency": curr_code,
                "currency_symbol": curr_sym,
                "max_guests": getattr(prop, "max_guests", 2) or 2,
                "bedrooms": getattr(prop, "bedrooms", 1) or 1,
                "bathrooms": getattr(prop, "bathrooms", 1) or 1,
                "rating": round(float(avg_rating), 1),
                "review_count": review_count,
                "cover_image": cover_image,
                "property_type": prop_type_str,
            })

        total_val = getattr(page_result, "total", len(items_data))
        if not isinstance(total_val, int):
            try:
                total_val = int(total_val)
            except Exception:
                total_val = len(items_data)

        page_val = getattr(page_result, "page", page)
        if not isinstance(page_val, int):
            try:
                page_val = int(page_val)
            except Exception:
                page_val = page

        page_size_val = getattr(page_result, "page_size", page_size)
        if not isinstance(page_size_val, int):
            try:
                page_size_val = int(page_size_val)
            except Exception:
                page_size_val = page_size

        total_pages = getattr(page_result, "pages", 1)
        if not isinstance(total_pages, int):
            try:
                total_pages = int(total_pages)
            except Exception:
                total_pages = (total_val + page_size_val - 1) // page_size_val if total_val > 0 else 1

        summary_text = (
            f"Found {total_val} homestay(s) matching criteria. Showing page {page_val} of {total_pages}."
        )

        return CallToolResult(
            content=[TextContent(text=summary_text + "\n" + json.dumps(items_data, indent=2))],
            isError=False,
            data={
                "total": total_val,
                "page": page_val,
                "page_size": page_size_val,
                "total_pages": total_pages,
                "properties": items_data,
            },
        )

    async def _handle_semantic_search_homestays(self, args: Dict[str, Any]) -> CallToolResult:
        query = args.get("query", "").strip()
        if not query:
            raise AppException(400, "query is required for semantic search.", error_code="QUERY_REQUIRED")

        city_name = args.get("city_name")
        min_price = args.get("min_price")
        max_price = args.get("max_price")
        prop_type = args.get("property_type")
        limit = min(args.get("limit", 8), 25)
        min_similarity = args.get("min_similarity")

        vector_results = []
        if self.vector_search_service:
            # Auto-index active properties if index is empty
            if self.vector_search_service.total_indexed == 0 and self.property_service:
                try:
                    all_stays = await self.property_service.get_all(
                        is_active=True,
                        page=1,
                        page_size=100,
                        with_relations={
                            "city": True,
                            "location": True,
                            "property_assets": True,
                            "property_amenities": True,
                        },
                    )
                    items = getattr(all_stays, "items", all_stays) or []
                    if items:
                        await self.vector_search_service.index_properties(items)
                except Exception as e:
                    logger.warning("Auto-indexing for semantic search encountered: %s", e)

            vector_results = await self.vector_search_service.search(
                query=query,
                city_name=city_name,
                min_price=min_price,
                max_price=max_price,
                property_type=prop_type,
                limit=limit,
                min_similarity=min_similarity,
            )

        if vector_results:
            summary_text = f"Found {len(vector_results)} homestay(s) matching vibe/semantic criteria: '{query}'."
            return CallToolResult(
                content=[TextContent(text=summary_text + "\n" + json.dumps(vector_results, indent=2))],
                isError=False,
                data={
                    "total": len(vector_results),
                    "query": query,
                    "properties": vector_results,
                },
            )

        # Fallback to standard search if no vector results or service disabled
        return await self._handle_search_homestays(args)

    async def _handle_check_availability(self, args: Dict[str, Any]) -> CallToolResult:
        prop_id = args.get("property_id")
        check_in = self._parse_date(args.get("check_in_date"))
        check_out = self._parse_date(args.get("check_out_date"))
        num_guests = args.get("num_guests", 1)
        num_rooms = args.get("num_rooms", 1)
        room_type_id_arg = args.get("room_type_id") or args.get("room_type")

        if not prop_id:
            raise AppException(400, "property_id is required.", error_code="PROPERTY_REQUIRED")
        if not check_in or not check_out:
            raise AppException(400, "Valid check_in_date and check_out_date are required (YYYY-MM-DD).", error_code="DATES_REQUIRED")
        if check_in < date.today():
            raise AppException(400, f"Check-in date {check_in.isoformat()} cannot be in the past.", error_code="PAST_CHECK_IN")
        if check_out <= check_in:
            raise AppException(400, "check_out_date must be after check_in_date.", error_code="INVALID_DATE_RANGE")

        prop = await self._resolve_property(prop_id)
        if not prop:
            raise AppException(404, f"Homestay '{prop_id}' not found.", error_code="PROPERTY_NOT_FOUND")

        room_type_id_db = await self._resolve_room_type(prop, room_type_id_arg)

        availability = await self.booking_service.check_availability(
            property_id=prop.id,
            room_type_id=room_type_id_db,
            check_in_date=check_in,
            check_out_date=check_out,
            num_rooms=num_rooms,
        )

        tax_rate, is_inclusive, tax_name, tax_code = await self._resolve_tax_settings()
        quote = self.booking_service.calculate_pricing_quote(
            property_=prop,
            check_in_date=check_in,
            check_out_date=check_out,
            num_rooms=num_rooms,
            num_guests=num_guests,
            room_type_id=room_type_id_db,
            tax_rate=tax_rate,
            is_tax_inclusive=is_inclusive,
            tax_name=tax_name,
            tax_code=tax_code,
        )

        nights = quote.get("nights", quote.get("num_nights", max(1, (check_out - check_in).days)))
        base_amount = quote.get("base_amount", quote.get("subtotal", 0.0))
        raw_curr = quote.get("currency") or (prop.currency if prop else None)
        curr_code, curr_sym = await self._resolve_currency_and_symbol(raw_curr)
        price_per_night = quote.get("price_per_night", 0.0)
        discount_amount = quote.get("discount_amount", 0.0)
        tax_amount = quote.get("tax_amount", 0.0)
        total_amount = quote.get("total_amount", 0.0)

        fmt_cin = await self._format_date(check_in)
        fmt_cout = await self._format_date(check_out)

        # Build list of available room types with room-wise pricing & occupancy tiers
        room_types_breakdown = []
        selected_rt_name = None
        selected_rt_capacity = getattr(prop, "max_guests", 2) or 2
        max_single_room_cap = getattr(prop, "max_guests", 2) or 2
        total_prop_units = 0

        if hasattr(prop, "property_room_types") and prop.property_room_types:
            for prt in prop.property_room_types:
                rt_name = prt.room_type.name if hasattr(prt, "room_type") and prt.room_type else "Standard Room"
                rt_pub_id = str(prt.room_type.public_id) if hasattr(prt, "room_type") and prt.room_type else str(prt.room_type_id)
                prt_sale = float(prt.sale_per_night) if prt.sale_per_night is not None else 0.0
                prt_price = float(prt.price_per_night) if prt.price_per_night is not None else 0.0
                effective_price = prt_sale if prt_sale > 0 and (prt_price == 0 or prt_sale < prt_price) else (prt_price or float(prop.price_per_night or 0))
                is_sel = (prt.room_type_id == room_type_id_db) if room_type_id_db else False
                cap = getattr(prt.room_type, "capacity", getattr(prop, "max_guests", 2)) if hasattr(prt, "room_type") and prt.room_type else 2
                max_single_room_cap = max(max_single_room_cap, cap)
                total_prop_units += (prt.total_units or 1)

                if is_sel:
                    selected_rt_name = rt_name
                    selected_rt_capacity = cap

                # Extract occupancy-based pricing tiers (e.g. 2 guests: ₹1,500, 3 guests: ₹1,550, 4 guests: ₹1,600)
                tiers_list = []
                if hasattr(prt, "pricing_tiers") and prt.pricing_tiers:
                    sorted_tiers = sorted(list(prt.pricing_tiers), key=lambda t: t.occupancy)
                    for t in sorted_tiers:
                        t_sale = float(t.sale_per_night) if t.sale_per_night is not None else 0.0
                        t_price = float(t.price_per_night) if t.price_per_night is not None else 0.0
                        eff_t = t_sale if t_sale > 0 and (t_price == 0 or t_sale < t_price) else t_price
                        tiers_list.append({
                            "id": str(getattr(t, "public_id", t.id)),
                            "occupancy": t.occupancy,
                            "price_per_night": eff_t,
                            "base_price": t_price,
                            "sale_per_night": t_sale,
                        })

                room_types_breakdown.append({
                    "id": rt_pub_id,
                    "property_room_type_id": str(getattr(prt, "public_id", prt.id)),
                    "name": rt_name,
                    "price_per_night": effective_price,
                    "total_units": prt.total_units,
                    "available_units": prt.total_units,
                    "max_rooms": prt.total_units,
                    "capacity": cap,
                    "max_guests": cap,
                    "pricing_tiers": tiers_list,
                    "is_selected": is_sel,
                })

        if not selected_rt_name and room_types_breakdown:
            selected_rt_name = room_types_breakdown[0]["name"]
            selected_rt_capacity = room_types_breakdown[0].get("capacity", 2)

        avail_units = availability.get("available_units", 1)
        max_selectable_guests = max_single_room_cap * max(1, avail_units)
        max_selectable_rooms = max(1, avail_units)

        applied_tier = quote.get("applied_tier")
        response_payload = {
            "property_name": prop.name,
            "property_slug": prop.slug,
            "selected_room_type": selected_rt_name,
            "room_types": room_types_breakdown,
            "room_types_availability": availability.get("room_types_availability", []),
            "applied_tier": applied_tier,
            "is_available": availability["is_available"],
            "available_units": availability["available_units"],
            "requested_rooms": num_rooms,
            "max_guests": max_selectable_guests,
            "max_rooms": max_selectable_rooms,
            "capacity": selected_rt_capacity,
            "max_capacity_per_room": selected_rt_capacity,
            "total_units": total_prop_units or avail_units,
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat(),
            "formatted_check_in_date": fmt_cin,
            "formatted_check_out_date": fmt_cout,
            "num_nights": nights,
            "nights": nights,
            "price_per_night": float(price_per_night),
            "subtotal": float(base_amount),
            "base_amount": float(base_amount),
            "discount_amount": float(discount_amount),
            "tax_amount": float(tax_amount),
            "total_amount": float(total_amount),
            "currency": curr_code,
            "currency_symbol": curr_sym,
        }

        status_msg = "Available for booking!" if availability["is_available"] else f"Unavailable. Only {availability['available_units']} room(s) available."
        rt_label = f" ({selected_rt_name})" if selected_rt_name else ""
        tier_tag = f" [{applied_tier['occupancy']} Guest Tier Active: {curr_sym} {applied_tier['price_per_night']}/night]" if applied_tier else ""
        text = f"{prop.name}{rt_label} - {status_msg}{tier_tag}\nDates: {fmt_cin} to {fmt_cout} ({nights} nights) | Total: {curr_sym} {total_amount}"

        return CallToolResult(
            content=[TextContent(text=text)],
            isError=False,
            data=response_payload,
        )

    async def _handle_get_homestay_details(self, args: Dict[str, Any]) -> CallToolResult:
        prop_id = args.get("property_id")
        if not prop_id:
            raise AppException(400, "property_id is required.", error_code="PROPERTY_REQUIRED")

        prop = await self._resolve_property(prop_id)
        if not prop:
            raise AppException(404, f"Homestay '{prop_id}' not found.", error_code="PROPERTY_NOT_FOUND")

        room_types = []
        total_prop_units = 0
        max_single_cap = getattr(prop, "max_guests", 2) or 2
        if hasattr(prop, "property_room_types") and prop.property_room_types:
            for prt in prop.property_room_types:
                rt_name = prt.room_type.name if hasattr(prt, "room_type") and prt.room_type else "Standard Room"
                rt_pub_id = str(prt.room_type.public_id) if hasattr(prt, "room_type") and prt.room_type else str(prt.room_type_id)
                prt_sale = float(prt.sale_per_night) if prt.sale_per_night is not None else 0.0
                prt_price = float(prt.price_per_night) if prt.price_per_night is not None else 0.0
                effective_price = prt_sale if prt_sale > 0 and (prt_price == 0 or prt_sale < prt_price) else (prt_price or float(prop.price_per_night or prop.base_price or 0))
                cap = getattr(prt.room_type, "capacity", getattr(prop, "max_guests", 2)) if hasattr(prt, "room_type") and prt.room_type else 2
                max_single_cap = max(max_single_cap, cap)
                total_prop_units += (prt.total_units or 1)

                tiers_list = []
                if hasattr(prt, "pricing_tiers") and prt.pricing_tiers:
                    sorted_tiers = sorted(list(prt.pricing_tiers), key=lambda t: t.occupancy)
                    for t in sorted_tiers:
                        t_sale = float(t.sale_per_night) if t.sale_per_night is not None else 0.0
                        t_price = float(t.price_per_night) if t.price_per_night is not None else 0.0
                        eff_t = t_sale if t_sale > 0 and (t_price == 0 or t_sale < t_price) else t_price
                        tiers_list.append({
                            "id": str(getattr(t, "public_id", t.id)),
                            "occupancy": t.occupancy,
                            "price_per_night": eff_t,
                            "base_price": t_price,
                            "sale_per_night": t_sale,
                        })

                room_types.append({
                    "id": rt_pub_id,
                    "property_room_type_id": str(getattr(prt, "public_id", prt.id)),
                    "room_type_id": prt.room_type_id,
                    "name": rt_name,
                    "total_units": prt.total_units,
                    "max_rooms": prt.total_units,
                    "price_per_night": effective_price,
                    "base_price": effective_price,
                    "capacity": cap,
                    "max_guests": cap,
                    "pricing_tiers": tiers_list,
                })

        amenities = []
        if hasattr(prop, "property_amenities") and prop.property_amenities:
            for pa in prop.property_amenities:
                if hasattr(pa, "amenity") and pa.amenity:
                    amenities.append(pa.amenity.name)

        facilities = []
        if hasattr(prop, "property_facilities") and prop.property_facilities:
            for pf in prop.property_facilities:
                if hasattr(pf, "facility") and pf.facility:
                    facilities.append(pf.facility.name)

        policy_info = None
        if hasattr(prop, "cancellation_policy") and prop.cancellation_policy:
            policy = prop.cancellation_policy
            policy_info = {
                "name": policy.name,
                "description": policy.description,
                "refund_percentage": float(policy.refund_percentage) if policy.refund_percentage else None,
                "days_before_checkin": policy.days_before_checkin,
            }

        raw_price = getattr(prop, "sale_per_night", None) or getattr(prop, "price_per_night", None) or getattr(prop, "base_price", None)
        base_price = float(raw_price) if raw_price is not None else 0.0

        curr_code, curr_sym = await self._resolve_currency_and_symbol(getattr(prop, "currency", None))

        rating_summary = {"average_rating": 0.0, "total_reviews": 0, "rating_distribution": {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}}
        recent_reviews = []
        if self.review_service:
            try:
                summary = await self.review_service.get_property_rating_summary(prop.id)
                if summary:
                    rating_summary = summary

                rev_page = await self.review_service.list_by_property(prop.id, status="published", page=1, page_size=5, with_relations={"guest": True})
                rev_items = getattr(rev_page, "items", rev_page) or []
                for r in rev_items:
                    g_name = r.guest.full_name if hasattr(r, "guest") and r.guest else "Guest"
                    g_avatar = getattr(r.guest, "avatar_url", None) if hasattr(r, "guest") and r.guest else None
                    created_str = await self._format_date(getattr(r, "created_at", None))
                    recent_reviews.append({
                        "id": str(getattr(r, "public_id", r.id)),
                        "rating": float(r.rating) if r.rating is not None else 0.0,
                        "comment": r.comment,
                        "guest_name": g_name,
                        "guest_avatar": g_avatar,
                        "created_at": created_str,
                    })
            except Exception as e:
                logger.warning("Could not load reviews for property %s: %s", prop.id, e)

        details = {
            "id": str(getattr(prop, "public_id", prop.id)),
            "name": prop.name,
            "slug": prop.slug,
            "description": getattr(prop, "description", None),
            "city": prop.city.name if getattr(prop, "city", None) and hasattr(prop.city, "name") else None,
            "location": prop.location.name if getattr(prop, "location", None) and hasattr(prop.location, "name") else None,
            "address": getattr(prop, "address", None),
            "base_price": base_price,
            "currency": curr_code,
            "currency_symbol": curr_sym,
            "max_guests": max_single_cap,
            "max_rooms": total_prop_units or 1,
            "total_units": total_prop_units or 1,
            "bedrooms": getattr(prop, "bedrooms", 1) or 1,
            "bathrooms": getattr(prop, "bathrooms", 1) or 1,
            "rating": round(float(rating_summary.get("average_rating", 0.0)), 1),
            "review_count": int(rating_summary.get("total_reviews", 0)),
            "rating_distribution": rating_summary.get("rating_distribution", {}),
            "recent_reviews": recent_reviews,
            "check_in_time": str(getattr(prop, "check_in_time", "14:00")) or "14:00",
            "check_out_time": str(getattr(prop, "check_out_time", "11:00")) or "11:00",
            "room_types": room_types,
            "amenities": amenities,
            "facilities": facilities,
            "cancellation_policy": policy_info,
        }


        return CallToolResult(
            content=[TextContent(text=f"Homestay details for {prop.name}:\n" + json.dumps(details, indent=2))],
            isError=False,
            data=details,
        )

    async def _handle_register_guest_user(self, args: Dict[str, Any]) -> CallToolResult:
        full_name = (args.get("full_name") or "").strip()
        email = (args.get("email") or "").strip().lower()
        phone = (args.get("phone") or "").strip()
        password = args.get("password") or "TashiHome@" + datetime.now().strftime("%Y%m")

        if not full_name or not email or not phone:
            raise AppException(400, "full_name, email, and phone are required for registration.", error_code="MISSING_FIELDS")

        existing_user = await self.user_service.get_user_by_email(email)
        if existing_user:
            return CallToolResult(
                content=[TextContent(text=f"User already registered with email {email}. Proceeding with existing account.")],
                isError=False,
                data={
                    "user_id": existing_user.id,
                    "public_id": str(existing_user.public_id),
                    "full_name": existing_user.full_name,
                    "email": existing_user.email,
                    "is_new": False,
                },
            )

        hashed_password = await self.password_hasher.hash_password(password)
        new_user = User(
            full_name=full_name,
            email=email,
            phone=phone,
            password=hashed_password,
            role=UserRole.USER,
            status=UserStatus.ACTIVE,
            is_subscribed=bool(args.get("is_subscribed", False)),
            is_terms_accepted=True,
        )

        user = await self.user_service.create_user(new_user)
        if self.event_bus:
            try:
                await self.event_bus.publish(CreateUserEvent(user))
            except Exception as e:
                logger.warning("Failed to publish CreateUserEvent: %s", e)

        return CallToolResult(
            content=[TextContent(text=f"Guest account successfully created for {user.full_name} ({user.email}).")],
            isError=False,
            data={
                "user_id": user.id,
                "id": str(user.public_id),
                "public_id": str(user.public_id),
                "full_name": user.full_name,
                "email": user.email,
                "phone": user.phone,
                "is_new": True,
            },
        )

    async def _handle_checkout_and_book(
        self,
        args: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> CallToolResult:
        if not settings.PAYMENT_ENABLED:
            raise AppException(
                status_code=400,
                message="Booking creation is currently disabled because payment processing is turned off by platform configuration.",
                error_code="PAYMENT_DISABLED",
            )

        prop_id = args.get("property_id")
        check_in = self._parse_date(args.get("check_in_date"))
        check_out = self._parse_date(args.get("check_out_date"))
        num_guests = args.get("num_guests", 1)
        num_rooms = args.get("num_rooms", 1)
        room_type_id_arg = args.get("room_type_id")
        special_requests = args.get("special_requests")

        guest_name = args.get("guest_name")
        guest_email = (args.get("guest_email") or "").strip().lower()
        guest_phone = args.get("guest_phone")
        guest_password = args.get("guest_password")

        if not prop_id:
            raise AppException(400, "property_id is required.", error_code="PROPERTY_REQUIRED")
        if not check_in or not check_out:
            raise AppException(400, "Valid check_in_date and check_out_date are required (YYYY-MM-DD).", error_code="DATES_REQUIRED")
        if check_in < date.today():
            raise AppException(400, "Check-in date cannot be in the past.", error_code="PAST_CHECK_IN")
        if check_out <= check_in:
            raise AppException(400, "check_out_date must be after check_in_date.", error_code="INVALID_DATE_RANGE")

        # 1. Identify or Auto-Register User
        user_id = current_user_id
        user_info = None

        if not user_id:
            if not guest_email:
                raise AppException(
                    400,
                    "guest_email is required for unauthenticated bookings to register or identify your reservation.",
                    error_code="GUEST_EMAIL_REQUIRED",
                )
            existing = await self.user_service.get_user_by_email(guest_email)
            if existing:
                user_id = existing.id
                user_info = existing
            else:
                if not guest_name or not guest_phone:
                    raise AppException(
                        400,
                        "guest_name and guest_phone are required to register your guest account for booking.",
                        error_code="REGISTRATION_DETAILS_REQUIRED",
                    )
                reg_result = await self._handle_register_guest_user({
                    "full_name": guest_name,
                    "email": guest_email,
                    "phone": guest_phone,
                    "password": guest_password,
                })
                user_id = reg_result.data["user_id"]
                user_info = await self.user_service.get_user_by_id(user_id)
        else:
            user_info = await self.user_service.get_user_by_id(user_id)

        # 2. Resolve Property & Room Type
        prop = await self._resolve_property(prop_id)
        if not prop:
            raise AppException(404, f"Homestay '{prop_id}' not found.", error_code="PROPERTY_NOT_FOUND")
        if prop.status != PropertyStatus.ACTIVE:
            raise AppException(400, "Homestay is currently not accepting new bookings.", error_code="PROPERTY_NOT_ACTIVE")

        room_type_id_db = await self._resolve_room_type(prop, room_type_id_arg)
        selected_rt_name = None
        if hasattr(prop, "property_room_types") and prop.property_room_types:
            for prt in prop.property_room_types:
                if prt.room_type_id == room_type_id_db:
                    selected_rt_name = prt.room_type.name if getattr(prt, "room_type", None) else None
                    break

        # 3. Check Availability
        availability = await self.booking_service.check_availability(
            property_id=prop.id,
            room_type_id=room_type_id_db,
            check_in_date=check_in,
            check_out_date=check_out,
            num_rooms=num_rooms,
        )
        if not availability.get("is_available") or availability.get("available_units", 0) < num_rooms:
            avail_cnt = availability.get("available_units", 0)
            raise AppException(
                400,
                f"Selected dates ({check_in.isoformat()} to {check_out.isoformat()}) are unavailable. Only {avail_cnt} room(s) available for {num_rooms} requested room(s). Booking cannot be created.",
                error_code="ROOMS_UNAVAILABLE",
            )

        # 4. Calculate Quote
        tax_rate, is_inclusive, tax_name, tax_code = await self._resolve_tax_settings()
        quote = self.booking_service.calculate_pricing_quote(
            property_=prop,
            check_in_date=check_in,
            check_out_date=check_out,
            num_rooms=num_rooms,
            num_guests=num_guests,
            room_type_id=room_type_id_db,
            tax_rate=tax_rate,
            is_tax_inclusive=is_inclusive,
            tax_name=tax_name,
            tax_code=tax_code,
        )

        # 5. Create Booking
        booking_ref = self.booking_service.generate_booking_reference()
        booking = Booking(
            booking_reference=booking_ref,
            guest_id=user_id,
            property_id=prop.id,
            room_type_id=room_type_id_db,
            cancellation_policy_id=prop.cancellation_policy_id,
            check_in_date=check_in,
            check_out_date=check_out,
            num_guests=num_guests,
            num_rooms=num_rooms,
            price_per_night=quote["price_per_night"],
            discount_amount=quote["discount_amount"],
            tax_amount=quote["tax_amount"],
            total_amount=quote["total_amount"],
            currency=quote["currency"],
            status=BookingStatus.PENDING,
            payment_status=PaymentStatus.PENDING,
            special_requests=special_requests,
            created_by=user_id,
        )

        created_booking = await self.booking_service.create_booking(
            booking=booking,
            with_relations={
                "guest": True,
                "property": True,
                "room_type": True,
                "cancellation_policy": True,
            },
        )

        guest_public_id = str(getattr(user_info, "public_id", user_id)) if user_info else str(user_id)
        nights = quote.get("nights", quote.get("num_nights", max(1, (check_out - check_in).days)))
        total_amount = float(quote.get("total_amount", 0.0))
        raw_currency = quote.get("currency") or (prop.currency if prop else None)
        curr_code, curr_sym = await self._resolve_currency_and_symbol(raw_currency)

        fmt_cin = await self._format_date(check_in)
        fmt_cout = await self._format_date(check_out)

        # Generate Payment Gateway Session / Order for checkout if payment is enabled
        gw_info = await self._generate_payment_gateway_order(
            booking=created_booking,
            amount=total_amount,
            user_id=user_id,
            payment_method="card",
        ) if settings.PAYMENT_ENABLED else None

        applied_tier = quote.get("applied_tier")
        result_payload = {
            "booking_reference": created_booking.booking_reference,
            "id": str(created_booking.public_id),
            "status": str(created_booking.status.value if hasattr(created_booking.status, "value") else created_booking.status),
            "payment_status": str(created_booking.payment_status.value if hasattr(created_booking.payment_status, "value") else created_booking.payment_status),
            "property_name": prop.name,
            "room_type_name": selected_rt_name,
            "applied_tier": applied_tier,
            "price_per_night": float(quote["price_per_night"]),
            "check_in_date": check_in.isoformat(),
            "check_out_date": check_out.isoformat(),
            "formatted_check_in_date": fmt_cin,
            "formatted_check_out_date": fmt_cout,
            "num_guests": num_guests,
            "num_rooms": num_rooms,
            "total_amount": total_amount,
            "currency": curr_code,
            "currency_symbol": curr_sym,
            "guest": {
                "id": guest_public_id,
                "full_name": user_info.full_name if user_info else guest_name,
                "email": user_info.email if user_info else guest_email,
            },
            "payment_gateway": gw_info,
        }

        rt_label = f" ({selected_rt_name})" if selected_rt_name else ""
        tier_label = f" [{applied_tier['occupancy']} Guest Tier: {curr_sym} {applied_tier['price_per_night']}/night]" if applied_tier else ""
        gw_text = (
            f"\n\n💳 **Payment Gateway Session Generated**:\n"
            f"• Gateway Order ID: `{gw_info['order_id']}`\n"
            f"• Payment Link: {gw_info['payment_url']}\n"
            f"Complete your payment to finalize this reservation."
        ) if gw_info else "\n\nℹ️ **Payment on Arrival**: Online payment gateway is currently disabled. You can settle your payment directly upon arrival at the homestay."

        confirmation_text = (
            f"🎉 Reservation confirmed! Booking Reference: **{created_booking.booking_reference}**\n"
            f"• Property: {prop.name}{rt_label}\n"
            f"• Rate: {curr_sym} {quote['price_per_night']}/night{tier_label}\n"
            f"• Dates: {fmt_cin} to {fmt_cout} ({nights} night(s))\n"
            f"• Total Amount: {curr_sym} {total_amount}\n"
            f"• Guest: {user_info.full_name if user_info else guest_name} ({user_info.email if user_info else guest_email})"
            f"{gw_text}"
        )

        return CallToolResult(
            content=[TextContent(text=confirmation_text)],
            isError=False,
            data=result_payload,
        )

    async def _generate_payment_gateway_order(
        self,
        booking: Booking,
        amount: float,
        user_id: Optional[int] = None,
        payment_method: str = "card",
    ) -> Dict[str, Any]:
        """Creates a Razorpay or gateway order session and registers an INITIATED payment."""
        order_amount = round(float(amount), 2)
        raw_currency = getattr(booking, "currency", None)
        currency, curr_sym = await self._resolve_currency_and_symbol(raw_currency)
        order_id: Optional[str] = None
        key_id = getattr(self.razorpay_service, "key_id", None) or settings.RAZORPAY_KEY_ID

        if self.razorpay_service and getattr(self.razorpay_service, "is_configured", lambda: False)() and settings.PAYMENT_ENABLED:
            try:
                razorpay_order = await self.razorpay_service.create_order(
                    amount=order_amount,
                    currency=currency,
                    receipt=booking.booking_reference,
                    notes={
                        "booking_id": str(booking.public_id),
                        "booking_reference": booking.booking_reference,
                        "guest_id": str(booking.guest_id or user_id or ""),
                    },
                )
                order_id = razorpay_order.get("id")
            except Exception as e:
                logger.warning("Razorpay order creation fallback: %s", e)

        if not order_id:
            order_id = f"order_{uuid4().hex[:16]}"

        frontend_base = (settings.FRONTEND_URL or "http://localhost:4200").rstrip("/")
        payment_url = f"{frontend_base}/bookings/{booking.booking_reference}/pay"

        # Record payment in database
        if self.payment_service and booking.id:
            try:
                pm_enum = None
                try:
                    pm_enum = PaymentMethod(payment_method.lower())
                except Exception:
                    pm_enum = PaymentMethod.CARD

                payment_record = Payment(
                    booking_id=booking.id,
                    amount=order_amount,
                    currency=currency,
                    payment_method=pm_enum,
                    gateway="razorpay",
                    transaction_id=order_id,
                    status=TransactionStatus.INITIATED,
                    refunded_amount=0,
                )
                await self.payment_service.create(payment_record)
            except Exception as e:
                logger.warning("Could not persist initiated payment record: %s", e)

        return {
            "gateway": "razorpay",
            "order_id": order_id,
            "key_id": key_id,
            "amount": order_amount,
            "currency": currency,
            "currency_symbol": curr_sym,
            "payment_url": payment_url,
            "status": "initiated",
        }

    async def _handle_initiate_booking_payment(
        self,
        args: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> CallToolResult:
        ref = (args.get("booking_reference") or "").strip()
        if not ref:
            raise AppException(400, "booking_reference is required.", error_code="BOOKING_REF_REQUIRED")

        booking = await self._find_booking(
            ref,
            with_relations={"property": True, "guest": True, "room_type": True, "payments": True},
        )

        if not settings.PAYMENT_ENABLED:
            raise AppException(
                400,
                "Online payment processing is currently disabled by configuration. Please complete your payment directly at the homestay upon arrival.",
                error_code="PAYMENT_DISABLED",
            )

        if not booking:
            raise AppException(404, f"Booking '{ref}' not found.", error_code="BOOKING_NOT_FOUND")

        if booking.status == BookingStatus.CANCELLED:
            raise AppException(400, "Cannot initiate payment for a cancelled booking.", error_code="BOOKING_CANCELLED")

        curr_code, curr_sym = await self._resolve_currency_and_symbol(booking.currency)

        if booking.payment_status == PaymentStatus.PAID:
            return CallToolResult(
                content=[TextContent(text=f"Booking **{booking.booking_reference}** is already fully paid.")],
                isError=False,
                data={
                    "booking_reference": booking.booking_reference,
                    "id": str(booking.public_id),
                    "status": str(booking.status.value if hasattr(booking.status, "value") else booking.status),
                    "payment_status": "paid",
                    "total_amount": float(booking.total_amount),
                    "remaining_balance": 0.0,
                    "currency": curr_code,
                    "currency_symbol": curr_sym,
                },
            )

        # Calculate remaining balance
        successful_payments = [
            p for p in (booking.payments or []) if p.status == TransactionStatus.SUCCESS
        ]
        total_paid_so_far = sum(float(p.amount) for p in successful_payments)
        remaining_balance = round(float(booking.total_amount) - total_paid_so_far, 2)

        req_amount = args.get("amount")
        order_amount = round(float(req_amount), 2) if req_amount is not None else remaining_balance
        if order_amount <= 0:
            order_amount = remaining_balance

        payment_method = args.get("payment_method") or "card"
        gw_info = await self._generate_payment_gateway_order(
            booking=booking,
            amount=order_amount,
            user_id=current_user_id or booking.guest_id,
            payment_method=payment_method,
        )

        prop_name = booking.property.name if hasattr(booking, "property") and booking.property else None
        response_data = {
            "booking_reference": booking.booking_reference,
            "id": str(booking.public_id),
            "property_name": prop_name,
            "status": str(booking.status.value if hasattr(booking.status, "value") else booking.status),
            "payment_status": str(booking.payment_status.value if hasattr(booking.payment_status, "value") else booking.payment_status),
            "total_amount": float(booking.total_amount),
            "remaining_balance": remaining_balance,
            "currency": curr_code,
            "currency_symbol": curr_sym,
            "payment_gateway": gw_info,
        }

        reply_msg = (
            f"Payment gateway session initiated for booking {booking.booking_reference}.\n"
            f"Amount due: {curr_sym} {remaining_balance:.2f} {curr_code}\n"
            f"Payment link: {gw_info['payment_url']}"
        )

        return CallToolResult(
            content=[TextContent(text=reply_msg)],
            isError=False,
            data=response_data,
        )

    async def _handle_get_booking_status(
        self,
        args: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> CallToolResult:
        ref = (args.get("booking_reference") or "").strip()
        if not ref:
            raise AppException(400, "booking_reference is required.", error_code="BOOKING_REF_REQUIRED")

        booking = await self._find_booking(
            ref,
            with_relations={"property": True, "guest": True, "room_type": True, "payments": True},
        )

        if not booking:
            raise AppException(404, f"Booking '{ref}' not found.", error_code="BOOKING_NOT_FOUND")

        curr_code, curr_sym = await self._resolve_currency_and_symbol(booking.currency)
        fmt_cin = await self._format_date(booking.check_in_date)
        fmt_cout = await self._format_date(booking.check_out_date)

        data = {
            "booking_reference": booking.booking_reference,
            "public_id": str(booking.public_id),
            "status": str(booking.status.value if hasattr(booking.status, "value") else booking.status),
            "payment_status": str(booking.payment_status.value if hasattr(booking.payment_status, "value") else booking.payment_status),
            "property_name": booking.property.name if hasattr(booking, "property") and booking.property else None,
            "check_in_date": booking.check_in_date.isoformat(),
            "check_out_date": booking.check_out_date.isoformat(),
            "formatted_check_in_date": fmt_cin,
            "formatted_check_out_date": fmt_cout,
            "num_guests": booking.num_guests,
            "num_rooms": booking.num_rooms,
            "total_amount": float(booking.total_amount),
            "currency": curr_code,
            "currency_symbol": curr_sym,
            "guest_name": booking.guest.full_name if hasattr(booking, "guest") and booking.guest else None,
        }

        return CallToolResult(
            content=[TextContent(text=f"Booking {booking.booking_reference}: Status={data['status']}, Payment={data['payment_status']}, Dates={fmt_cin} to {fmt_cout}, Total={curr_sym} {data['total_amount']}")],
            isError=False,
            data=data,
        )

    async def _handle_cancel_booking(
        self,
        args: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> CallToolResult:
        ref = (args.get("booking_reference") or "").strip()
        reason = args.get("reason", "Cancelled via AI Assistant")

        booking = await self._find_booking(ref)

        if not booking:
            raise AppException(404, f"Booking '{ref}' not found.", error_code="BOOKING_NOT_FOUND")

        cancelled = await self.booking_service.cancel_booking(
            booking=booking,
            cancelled_by=current_user_id or booking.guest_id,
            reason=reason,
        )

        return CallToolResult(
            content=[TextContent(text=f"Booking {cancelled.booking_reference} has been successfully cancelled.")],
            isError=False,
            data={
                "booking_reference": cancelled.booking_reference,
                "status": str(cancelled.status.value if hasattr(cancelled.status, "value") else cancelled.status),
                "cancellation_reason": reason,
            },
        )

    async def _handle_get_popular_destinations(self, args: Dict[str, Any]) -> CallToolResult:
        limit = min(args.get("limit", 6), 20)
        cities_list = []

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

                for c in (db_cities[:limit] if isinstance(db_cities, list) else []):
                    country_name = None
                    if getattr(c, "country", None) and hasattr(c.country, "name"):
                        country_name = c.country.name
                    cities_list.append({
                        "id": str(getattr(c, "public_id", c.slug)),
                        "name": c.name,
                        "slug": c.slug,
                        "description": getattr(c, "short_description", getattr(c, "tag_line", getattr(c, "description", None))),
                        "country": country_name,
                    })
            except Exception as e:
                logger.warning("Could not fetch popular destinations from DB: %s", e)

        platform_country = await self._resolve_platform_country()

        return CallToolResult(
            content=[TextContent(text=f"Popular Destinations:\n" + json.dumps(cities_list, indent=2))],
            isError=False,
            data={
                "destinations": cities_list,
                "country": platform_country,
            },
        )

