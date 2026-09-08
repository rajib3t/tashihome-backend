from typing import Dict, List, Optional

from app.mcp.protocol import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    PromptMessageContent,
)

TRIP_PLANNER_PROMPT = Prompt(
    name="homestay_trip_planner",
    description="Interactive assistant prompt to help travelers find the best authentic homestays based on their itinerary, party size, and preferences.",
    arguments=[
        PromptArgument(name="destination", description="City, region, or neighborhood destination", required=True),
        PromptArgument(name="guests", description="Number of travelers", required=False),
        PromptArgument(name="dates", description="Tentative travel dates", required=False),
        PromptArgument(name="budget", description="Budget level (budget, mid-range, luxury)", required=False),
    ],
)

BOOKING_CONCIERGE_PROMPT = Prompt(
    name="booking_concierge",
    description="Concierge guidance prompt to assist a guest through searching, checking availability, guest registration, and final checkout.",
    arguments=[
        PromptArgument(name="homestay_name_or_slug", description="The homestay they wish to book", required=True),
        PromptArgument(name="check_in_date", description="Check-in date", required=True),
        PromptArgument(name="check_out_date", description="Check-out date", required=True),
    ],
)

ALL_PROMPTS: List[Prompt] = [
    TRIP_PLANNER_PROMPT,
    BOOKING_CONCIERGE_PROMPT,
]


class MCPPromptHandler:
    async def list_prompts(self) -> List[Prompt]:
        return ALL_PROMPTS

    async def get_prompt(self, name: str, arguments: Optional[Dict[str, str]] = None) -> GetPromptResult:
        arguments = arguments or {}
        if name == "homestay_trip_planner":
            dest = arguments.get("destination", "our destinations")
            guests = arguments.get("guests", "2")
            dates = arguments.get("dates", "next weekend")
            budget = arguments.get("budget", "standard")

            system_text = (
                "You are the official Travel Concierge. Guide the guest to find ideal homestays. "
                "Use the search_homestays tool to retrieve live properties and recommend the top matches."
            )
            user_text = (
                f"I am planning a trip to {dest} for {guests} guest(s) around {dates}. My budget preference is {budget}. "
                f"Please search for homestays in {dest} and suggest the best options with prices and amenities."
            )

            return GetPromptResult(
                description=f"Trip planner for {dest}",
                messages=[
                    PromptMessage(role="system", content=PromptMessageContent(text=system_text)),
                    PromptMessage(role="user", content=PromptMessageContent(text=user_text)),
                ],
            )

        elif name == "booking_concierge":
            stay = arguments.get("homestay_name_or_slug", "the selected homestay")
            cin = arguments.get("check_in_date", "check-in date")
            cout = arguments.get("check_out_date", "check-out date")

            system_text = (
                "You are the TashiHome Booking Concierge. Help the guest verify availability and complete their checkout. "
                "If the guest is not registered, ask for their full name, email, and phone number to auto-register them seamlessly."
            )
            user_text = (
                f"I want to book {stay} from {cin} to {cout}. Please check availability, provide price quote, and guide me through checkout."
            )

            return GetPromptResult(
                description=f"Booking concierge for {stay}",
                messages=[
                    PromptMessage(role="system", content=PromptMessageContent(text=system_text)),
                    PromptMessage(role="user", content=PromptMessageContent(text=user_text)),
                ],
            )

        return GetPromptResult(
            description="Unknown prompt",
            messages=[
                PromptMessage(role="user", content=PromptMessageContent(text=f"Prompt '{name}' not recognized."))
            ],
        )

