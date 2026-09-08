from typing import Optional
from fastapi import Depends

from app.application.use_case.public.assistant.chat_assistant_use_case import ChatAssistantUseCase
from app.core.events import EventBus
from app.deps.event_bus import get_event_bus
from app.deps.service import (
    get_booking_service,
    get_city_service,
    get_country_service,
    get_location_service,
    get_payment_service,
    get_property_room_type_service,
    get_property_service,
    get_razorpay_service,
    get_review_service,
    get_room_type_service,
    get_setting_service,
    get_storage_service,
    get_tax_service,
    get_user_service,
)
from app.mcp.prompts import MCPPromptHandler
from app.mcp.resources import MCPResourceHandler
from app.mcp.server import TashiHomeMCPServer
from app.mcp.tools import MCPToolExecutor
from app.services.assistant_service import AssistantService
from app.services.booking_service import BookingService
from app.services.city_service import CityService
from app.services.country_service import CountryService
from app.services.embedding_service import EmbeddingService
from app.services.location_service import LocationService
from app.services.payment_service import PaymentService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.razorpay_service import RazorpayService
from app.services.review_service import ReviewService
from app.services.room_type_service import RoomTypeService
from app.services.setting_service import SettingService
from app.services.storage_service import StorageService
from app.services.tax_service import TaxService
from app.services.user_service import UserService
from app.services.vector_search_service import VectorSearchService


def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()


def get_vector_search_service(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    storage_service: StorageService = Depends(get_storage_service),
) -> VectorSearchService:
    return VectorSearchService.get_instance(
        embedding_service=embedding_service,
        storage_service=storage_service,
    )


def get_mcp_tool_executor(
    property_service: PropertyService = Depends(get_property_service),
    booking_service: BookingService = Depends(get_booking_service),
    user_service: UserService = Depends(get_user_service),
    payment_service: PaymentService = Depends(get_payment_service),
    razorpay_service: RazorpayService = Depends(get_razorpay_service),
    city_service: CityService = Depends(get_city_service),
    location_service: LocationService = Depends(get_location_service),
    country_service: CountryService = Depends(get_country_service),
    room_type_service: RoomTypeService = Depends(get_room_type_service),
    property_room_type_service: PropertyRoomTypeService = Depends(get_property_room_type_service),
    tax_service: TaxService = Depends(get_tax_service),
    setting_service: SettingService = Depends(get_setting_service),
    review_service: ReviewService = Depends(get_review_service),
    vector_search_service: VectorSearchService = Depends(get_vector_search_service),
    event_bus: EventBus = Depends(get_event_bus),
) -> MCPToolExecutor:
    return MCPToolExecutor(
        property_service=property_service,
        booking_service=booking_service,
        user_service=user_service,
        payment_service=payment_service,
        razorpay_service=razorpay_service,
        city_service=city_service,
        location_service=location_service,
        country_service=country_service,
        room_type_service=room_type_service,
        property_room_type_service=property_room_type_service,
        tax_service=tax_service,
        setting_service=setting_service,
        review_service=review_service,
        vector_search_service=vector_search_service,
        event_bus=event_bus,
    )


def get_mcp_server(
    tool_executor: MCPToolExecutor = Depends(get_mcp_tool_executor),
    city_service: CityService = Depends(get_city_service),
    country_service: CountryService = Depends(get_country_service),
    property_service: PropertyService = Depends(get_property_service),
) -> TashiHomeMCPServer:
    return TashiHomeMCPServer(
        tool_executor=tool_executor,
        resource_handler=MCPResourceHandler(
            city_service=city_service,
            country_service=country_service,
            property_service=property_service,
        ),
        prompt_handler=MCPPromptHandler(),
    )


def get_assistant_service(
    tool_executor: MCPToolExecutor = Depends(get_mcp_tool_executor),
) -> AssistantService:
    return AssistantService(tool_executor=tool_executor)


def get_chat_assistant_use_case(
    assistant_service: AssistantService = Depends(get_assistant_service),
) -> ChatAssistantUseCase:
    return ChatAssistantUseCase(assistant_service=assistant_service)


