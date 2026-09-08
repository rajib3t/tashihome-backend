from typing import Optional
from fastapi import APIRouter, Depends

from app.api.base_controller import BaseController
from app.application.dto.assistant.assistant import (
    AssistantChatRequestDTO,
    AssistantCheckoutDTO,
    AssistantSearchDTO,
    SemanticSearchRequestDTO,
)
from app.application.use_case.public.assistant.chat_assistant_use_case import ChatAssistantUseCase
from app.deps.assistant import (
    get_chat_assistant_use_case,
    get_mcp_tool_executor,
    get_vector_search_service,
)
from app.deps.auth import CurrentUser, get_optional_current_user
from app.deps.service import (
    get_city_service,
    get_country_service,
    get_property_service,
    get_setting_service,
)
from app.mcp.tools import MCPToolExecutor
from app.schemas.assistant_schema import (
    AssistantChatResponseSchema,
    AssistantSuggestionItemSchema,
    AssistantSuggestionsDataSchema,
    AssistantSuggestionsResponseSchema,
    AssistantToolCallSchema,
    SemanticSearchDataSchema,
    SemanticSearchResponseSchema,
    SemanticSearchResultItemSchema,
    VectorSyncDataSchema,
    VectorSyncResponseSchema,
    VectorS3PersistDataSchema,
    VectorS3PersistResponseSchema,
    VectorS3LoadDataSchema,
    VectorS3LoadResponseSchema,
)
from app.services.city_service import CityService
from app.services.country_service import CountryService
from app.services.property_service import PropertyService
from app.services.setting_service import SettingService
from app.services.vector_search_service import VectorSearchService
from app.utils.exception_decorate import handle_api_exceptions


class PublicAssistantController(BaseController):
    def __init__(self):
        super().__init__()
        self.router = APIRouter(
            prefix="/assistant",
            tags=["Public - AI Assistant"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("post", "/chat", self._chat, {"response_model": AssistantChatResponseSchema}),
            ("post", "/search", self._search, {"response_model": AssistantChatResponseSchema}),
            ("post", "/semantic-search", self._semantic_search, {"response_model": SemanticSearchResponseSchema}),
            ("post", "/sync-embeddings", self._sync_embeddings, {"response_model": VectorSyncResponseSchema}),
            ("post", "/vector-save-s3", self._save_vectors_s3, {"response_model": VectorS3PersistResponseSchema}),
            ("post", "/vector-load-s3", self._load_vectors_s3, {"response_model": VectorS3LoadResponseSchema}),
            ("post", "/checkout", self._checkout, {"response_model": AssistantChatResponseSchema}),
            ("get", "/suggestions", self._get_suggestions, {"response_model": AssistantSuggestionsResponseSchema}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _chat(
        self,
        data: AssistantChatRequestDTO,
        current_user: Optional[CurrentUser] = Depends(get_optional_current_user),
        use_case: ChatAssistantUseCase = Depends(get_chat_assistant_use_case),
    ):
        result = await use_case.execute(data=data, current_user=current_user)
        return self.build_response(
            message="Assistant response generated successfully.",
            data=result,
        )

    @handle_api_exceptions
    async def _search(
        self,
        data: AssistantSearchDTO,
        current_user: Optional[CurrentUser] = Depends(get_optional_current_user),
        tool_executor: MCPToolExecutor = Depends(get_mcp_tool_executor),
    ):
        user_id = current_user.id if current_user else None
        tool_args = {
            "query": data.query,
            "city_name": data.city_name,
            "location_name": data.location_name,
            "address": data.address,
            "check_in_date": data.check_in_date.isoformat() if data.check_in_date else None,
            "check_out_date": data.check_out_date.isoformat() if data.check_out_date else None,
            "guests": data.guests,
            "rooms": data.rooms,
            "min_price": data.min_price,
            "max_price": data.max_price,
            "property_type": data.property_type,
            "page": data.page,
            "page_size": data.page_size,
        }
        res = await tool_executor.execute_tool("search_homestays", tool_args, current_user_id=user_id)
        props = (res.data or {}).get("properties", [])
        total = (res.data or {}).get("total", len(props))

        reply_text = f"Found {total} homestays matching your criteria."
        data_payload = {
            "reply": reply_text,
            "intent": "search_homestays",
            "action_taken": "Executed search_homestays",
            "tool_calls": [
                AssistantToolCallSchema(
                    tool="search_homestays",
                    arguments=tool_args,
                    result=res.data,
                    is_error=res.isError,
                )
            ],
            "search_results": props,
            "suggested_actions": ["Check availability for first homestay", "Explore homestays in Paro", "Filter by price"],
        }
        return self.build_response(
            message="Homestays search completed.",
            data=data_payload,
        )

    @handle_api_exceptions
    async def _semantic_search(
        self,
        data: SemanticSearchRequestDTO,
        vector_service: VectorSearchService = Depends(get_vector_search_service),
        property_service: PropertyService = Depends(get_property_service),
    ):
        # Auto-sync if index is empty
        if vector_service.total_indexed == 0:
            try:
                all_stays = await property_service.get_all(
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
                    await vector_service.index_properties(items)
            except Exception:
                pass

        results = await vector_service.search(
            query=data.query,
            city_name=data.city_name,
            min_price=data.min_price,
            max_price=data.max_price,
            property_type=data.property_type,
            limit=data.limit,
            min_similarity=data.min_similarity,
        )

        items_schema = [SemanticSearchResultItemSchema(**item) for item in results]
        return self.build_response(
            message=f"Semantic vector search completed. Found {len(items_schema)} match(es).",
            data=SemanticSearchDataSchema(
                query=data.query,
                total_matches=len(items_schema),
                results=items_schema,
            ),
        )

    @handle_api_exceptions
    async def _sync_embeddings(
        self,
        vector_service: VectorSearchService = Depends(get_vector_search_service),
        property_service: PropertyService = Depends(get_property_service),
    ):
        all_stays = await property_service.get_all(
            is_active=True,
            page=1,
            page_size=200,
            with_relations={
                "city": True,
                "location": True,
                "property_assets": True,
                "property_amenities": True,
            },
        )
        items = getattr(all_stays, "items", all_stays) or []
        indexed_count = await vector_service.index_properties(items)
        last_synced = vector_service.last_synced_at.isoformat() if vector_service.last_synced_at else None

        s3_res = await vector_service.save_to_s3()

        return self.build_response(
            message=f"Successfully indexed {indexed_count} active homestay(s) into vector search engine.",
            data=VectorSyncDataSchema(
                indexed_count=indexed_count,
                total_indexed=vector_service.total_indexed,
                last_synced_at=last_synced,
                s3_persisted=s3_res.get("persisted", False),
                s3_bucket=s3_res.get("bucket"),
                s3_key=s3_res.get("key"),
            ),
        )

    @handle_api_exceptions
    async def _save_vectors_s3(
        self,
        vector_service: VectorSearchService = Depends(get_vector_search_service),
    ):
        s3_res = await vector_service.save_to_s3()
        last_synced = vector_service.last_synced_at.isoformat() if vector_service.last_synced_at else None
        return self.build_response(
            message=f"Vector embeddings saved to S3 bucket '{s3_res.get('bucket')}'.",
            data=VectorS3PersistDataSchema(
                success=s3_res.get("success", False),
                persisted=s3_res.get("persisted", False),
                bucket=s3_res.get("bucket", "tashihome-vector"),
                key=s3_res.get("key", "vectors/homestays_vector_index.json"),
                total_saved=s3_res.get("total_saved", 0),
                last_synced_at=last_synced,
            ),
        )

    @handle_api_exceptions
    async def _load_vectors_s3(
        self,
        vector_service: VectorSearchService = Depends(get_vector_search_service),
    ):
        loaded_count = await vector_service.load_from_s3()
        last_synced = vector_service.last_synced_at.isoformat() if vector_service.last_synced_at else None
        bucket = vector_service._get_s3_bucket()
        key = vector_service._get_s3_key()
        return self.build_response(
            message=f"Loaded {loaded_count} vector embedding(s) from S3 bucket '{bucket}'.",
            data=VectorS3LoadDataSchema(
                success=loaded_count > 0,
                loaded_count=loaded_count,
                total_indexed=vector_service.total_indexed,
                bucket=bucket,
                key=key,
                last_synced_at=last_synced,
            ),
        )

    @handle_api_exceptions
    async def _checkout(
        self,
        data: AssistantCheckoutDTO,
        current_user: Optional[CurrentUser] = Depends(get_optional_current_user),
        tool_executor: MCPToolExecutor = Depends(get_mcp_tool_executor),
    ):
        user_id = current_user.id if current_user else None
        tool_args = {
            "property_id": data.property_id,
            "check_in_date": data.check_in_date.isoformat(),
            "check_out_date": data.check_out_date.isoformat(),
            "num_guests": data.num_guests,
            "num_rooms": data.num_rooms,
            "room_type_id": data.room_type_id,
            "special_requests": data.special_requests,
            "guest_name": data.guest_name,
            "guest_email": str(data.guest_email) if data.guest_email else None,
            "guest_phone": data.guest_phone,
            "guest_password": data.guest_password,
        }
        res = await tool_executor.execute_tool("checkout_and_book", tool_args, current_user_id=user_id)
        if res.isError:
            return self.build_response(
                message="Checkout could not be completed.",
                data={
                    "reply": res.content[0].text if res.content else "Booking failed.",
                    "intent": "checkout_and_book",
                    "tool_calls": [
                        AssistantToolCallSchema(
                            tool="checkout_and_book",
                            arguments=tool_args,
                            result=res.data,
                            is_error=True,
                        )
                    ],
                },
            )

        booking_data = res.data or {}
        reply_text = f"Reservation confirmed! Your booking reference is {booking_data.get('booking_reference')}."
        return self.build_response(
            message="Checkout completed and booking confirmed.",
            data={
                "reply": reply_text,
                "intent": "checkout_and_book",
                "action_taken": "Created booking and registered guest user (if new)",
                "tool_calls": [
                    AssistantToolCallSchema(
                        tool="checkout_and_book",
                        arguments=tool_args,
                        result=booking_data,
                        is_error=False,
                    )
                ],
                "booking": booking_data,
                "suggested_actions": ["Track booking status", "Cancellation policy", "Explore local attractions"],
            },
        )

    @handle_api_exceptions
    async def _get_suggestions(
        self,
        city_service: CityService = Depends(get_city_service),
        country_service: CountryService = Depends(get_country_service),
        setting_service: SettingService = Depends(get_setting_service),
        property_service: PropertyService = Depends(get_property_service),
    ):
        # Resolve active / featured cities
        active_cities: list[str] = []
        try:
            featured = await city_service.get_city_with_is_featured()
            if featured:
                active_cities.extend([c.name for c in featured if getattr(c, "name", None)])
            if len(active_cities) < 2:
                all_cities = await city_service.get_all()
                if hasattr(all_cities, "items"):
                    all_cities = all_cities.items
                for c in (all_cities or []):
                    c_name = getattr(c, "name", None)
                    if c_name and c_name not in active_cities:
                        active_cities.append(c_name)
        except Exception:
            pass

        # Resolve country name
        country_name = ""
        try:
            country_setting = await setting_service.get_by_key("site_country")
            if country_setting and getattr(country_setting, "value", None):
                country_name = str(country_setting.value).strip()
            if not country_name:
                countries = await country_service.get_all()
                if hasattr(countries, "items"):
                    countries = countries.items
                if countries:
                    country_name = getattr(countries[0], "name", "") or ""
        except Exception:
            pass

        # Resolve sample property name
        sample_prop_name = ""
        try:
            props = await property_service.list(page=1, page_size=1)
            items = getattr(props, "items", []) or []
            if items:
                sample_prop_name = getattr(items[0], "name", "") or ""
        except Exception:
            pass

        c1 = active_cities[0] if len(active_cities) > 0 else "Featured"
        c2 = active_cities[1] if len(active_cities) > 1 else (active_cities[0] if len(active_cities) > 0 else "Scenic")

        prop_label = sample_prop_name or "our featured homestay"
        dest_label = f" in {country_name}" if country_name else ""
        dest_q_label = f" in {country_name}" if country_name else ""

        suggestions = [
            AssistantSuggestionItemSchema(
                title=f"Discover {c1} Homestays",
                prompt=f"Find top rated homestays in {c1} for 2 guests next weekend.",
                category="search",
            ),
            AssistantSuggestionItemSchema(
                title=f"Scenic {c2} Stays",
                prompt=f"Show peaceful homestays in {c2} close to nature.",
                category="search",
            ),
            AssistantSuggestionItemSchema(
                title="Check Stay Availability",
                prompt=f"Check availability for {prop_label} for 2 guests from next Friday to Sunday.",
                category="booking",
            ),
            AssistantSuggestionItemSchema(
                title="Track My Booking",
                prompt="Check the status of my booking reference BK-...",
                category="booking",
            ),
            AssistantSuggestionItemSchema(
                title=f"Popular Destinations{dest_label}",
                prompt=f"What are the most popular travel destinations and homestay locations{dest_q_label}?",
                category="explore",
            ),
        ]
        return self.build_response(
            message="Suggestions fetched successfully.",
            data=AssistantSuggestionsDataSchema(suggestions=suggestions),
        )


controller = PublicAssistantController()
router = controller.router

