import asyncio
import json
import logging
import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import uuid4

try:
    import boto3
except ImportError:
    boto3 = None
import httpx

from app.core.config import settings
from app.core.exceptions import AppException
from app.mcp.tools import ALL_MCP_TOOLS, MCPToolExecutor
from app.schemas.assistant_schema import AssistantChatDataSchema, AssistantToolCallSchema

logger = logging.getLogger(__name__)

DEFAULT_SYSTEM_INSTRUCTION = """You are Tashi, the AI Travel Concierge for TashiHome (the premier homestay booking platform).

CRITICAL INSTRUCTIONS FOR TOOL EXECUTION & RESPONSE FORMATTING:
1. ALWAYS use the `search_homestays` or `semantic_search_homestays` tool whenever a user asks to search, find, or explore homestays, accommodations, rooms, or destinations.
   - You can search by destination/city, specific location/neighborhood, or street address.
   - Always invoke a search tool first to query the live database.
2. WHEN HOMESTAYS ARE RETURNED:
   - Provide a warm, well-formatted response listing each homestay with:
     * Name, city, specific location/neighborhood, and address
     * Nightly rate with setting-driven currency symbol (e.g. Nu., ₹, $)
     * Rating and key features/amenities
   - Prompt the user to check availability for specific dates or proceed with booking.
3. WHEN 0 HOMESTAYS ARE FOUND (e.g. non-served locations or unavailable dates):
   - Explicitly state that 0 matching homestays were found for that location.
   - Suggest exploring available featured destinations and cities from our platform listings.
4. DATE HANDLING & CAPACITY-BASED OCCUPANCY PRICING FOR AVAILABILITY & BOOKING:
   - Each homestay offers specific room types with capacity-based variable pricing tiers (e.g., Room Rates by Occupancy: 2 Guests: ₹1,500, 3 Guests: ₹1,550, 4 Guests: ₹1,600).
   - When presenting room types or answering inquiries about rates/availability, ALWAYS list the room type along with its maximum capacity and the full breakdown of occupancy-wise rates.
   - When checking availability or calculating quotes, highlight the active guest occupancy tier applied (e.g., '✓ 2 Guest Tier Active: ₹1,500/night').
   - If a user asks to check availability or checkout/book without specifying dates or room type, query the property details, present the available room types with their full occupancy pricing tiers, and politely ASK the user for:
     1. Check-in & Check-out dates
     2. Number of guests and rooms
     3. Preferred Room Type
   - DO NOT hallucinate, fabricate, or pick past or arbitrary dates.
5. CHECKOUT & PAYMENT GATEWAY:
   - If a guest wants to book or checkout with dates, property, and room type, call `checkout_and_book` (passing `room_type_id` / room type name if specified).
   - After checkout completes, present the booking reference, homestay name, room type booked, total amount, and direct payment gateway details (Order ID and payment link) so the guest can complete their payment securely.
6. INITIATE PAYMENT:
   - If a guest asks how to pay for an existing booking, asks for a payment link, or wants to initiate checkout payment for a reservation reference (e.g., 'Pay for BK-XXXX' or 'Generate payment link'), call `initiate_booking_payment`.
7. If a guest asks about an existing booking, call `get_booking_status`.
8. If a guest asks to cancel, call `cancel_booking`.
9. If a guest asks about popular destinations, call `get_popular_destinations`.
10. Tone: Warm, respectful, authentic hospitality (Tashi Delek!), concise, helpful, and transparent. NEVER reply with just a generic one-liner like "Here is what I found for you."
"""


class AssistantService:
    """Multi-provider AI Assistant engine integrated with Model Context Protocol (MCP) tools (Bedrock Nova Lite, Gemini, OpenAI)."""

    def __init__(
        self,
        tool_executor: MCPToolExecutor,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        bedrock_region: Optional[str] = None,
        bedrock_access_key_id: Optional[str] = None,
        bedrock_secret_access_key: Optional[str] = None,
        bedrock_session_token: Optional[str] = None,
    ):
        self.tool_executor = tool_executor
        self.system_instruction = settings.AI_SYSTEM_INSTRUCTION or DEFAULT_SYSTEM_INSTRUCTION
        self.provider = (provider or getattr(settings, "AI_PROVIDER", "gemini") or "gemini").lower()
        default_model = (
            getattr(settings, "BEDROCK_NOVA_MODEL_ID", "amazon.nova-lite-v1:0")
            if self.provider in {"bedrock", "aws", "nova"}
            else getattr(settings, "AI_MODEL", "gemini-1.5-flash")
        )
        self.model = model or default_model
        self.gemini_key = gemini_api_key or getattr(settings, "GEMINI_API_KEY", None)
        self.openai_key = openai_api_key or getattr(settings, "OPENAI_API_KEY", None)
        self.bedrock_region = bedrock_region or getattr(settings, "BEDROCK_AWS_REGION", "us-east-1")
        self.bedrock_access_key_id = (
            bedrock_access_key_id
            or getattr(settings, "BEDROCK_AWS_ACCESS_KEY_ID", None)
            or getattr(settings, "AWS_ACCESS_KEY_ID", None)
            or getattr(settings, "S3_ACCESS_KEY", None)
        )
        self.bedrock_secret_access_key = (
            bedrock_secret_access_key
            or getattr(settings, "BEDROCK_AWS_SECRET_ACCESS_KEY", None)
            or getattr(settings, "AWS_SECRET_ACCESS_KEY", None)
            or getattr(settings, "S3_SECRET_KEY", None)
        )
        self.bedrock_session_token = (
            bedrock_session_token
            or getattr(settings, "BEDROCK_AWS_SESSION_TOKEN", None)
            or getattr(settings, "AWS_SESSION_TOKEN", None)
        )
        self._bedrock_client = None

    def _get_bedrock_client(self):
        if self._bedrock_client is not None:
            return self._bedrock_client
        if boto3 is None:
            raise RuntimeError("boto3 is required for Amazon Bedrock integration. Please install boto3.")
        kwargs = {"region_name": self.bedrock_region}
        if self.bedrock_access_key_id and self.bedrock_secret_access_key:
            kwargs["aws_access_key_id"] = self.bedrock_access_key_id
            kwargs["aws_secret_access_key"] = self.bedrock_secret_access_key
            if self.bedrock_session_token:
                kwargs["aws_session_token"] = self.bedrock_session_token
        self._bedrock_client = boto3.client("bedrock-runtime", **kwargs)
        return self._bedrock_client

    # --------------------------------------------------------------------------
    # Main Chat Entrypoint
    # --------------------------------------------------------------------------

    async def chat(
        self,
        message: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
        session_id: Optional[str] = None,
        current_user_id: Optional[int] = None,
        guest_details: Optional[Dict[str, Any]] = None,
    ) -> AssistantChatDataSchema:
        """Process chat message with LLM function calling and MCP tool execution."""
        clean_msg = (message or "").strip()
        if not clean_msg:
            raise AppException(
                status_code=400,
                message="Chat message cannot be empty.",
                error_code="EMPTY_MESSAGE",
                field="message",
            )
        if len(clean_msg) > 4000:
            clean_msg = clean_msg[:4000]
        message = clean_msg

        session_id = session_id or str(uuid4())
        conversation_history = conversation_history or []
        guest_details = guest_details or {}

        # 1. Try Amazon Bedrock (Nova Lite) if configured
        if self.provider in {"bedrock", "aws", "nova"}:
            try:
                return await self._chat_with_bedrock(
                    message=message,
                    history=conversation_history,
                    session_id=session_id,
                    current_user_id=current_user_id,
                    guest_details=guest_details,
                )
            except Exception as e:
                logger.warning("Amazon Bedrock Nova call failed, falling back to intent engine: %s", e)

        # 2. Try Gemini Provider if API key is set
        elif self.provider == "gemini" and self.gemini_key:
            try:
                return await self._chat_with_gemini(
                    message=message,
                    history=conversation_history,
                    session_id=session_id,
                    current_user_id=current_user_id,
                    guest_details=guest_details,
                )
            except Exception as e:
                logger.warning("Gemini LLM call failed, falling back to intent engine: %s", e)

        # 3. Try OpenAI Provider if API key is set
        elif self.provider == "openai" and self.openai_key:
            try:
                return await self._chat_with_openai(
                    message=message,
                    history=conversation_history,
                    session_id=session_id,
                    current_user_id=current_user_id,
                    guest_details=guest_details,
                )
            except Exception as e:
                logger.warning("OpenAI LLM call failed, falling back to intent engine: %s", e)

        # 4. Deterministic NLP / Intent Engine Fallback (ensures 100% offline & test reliability)
        return await self._chat_with_intent_fallback(
            message=message,
            history=conversation_history,
            session_id=session_id,
            current_user_id=current_user_id,
            guest_details=guest_details,
        )

    @classmethod
    def _clean_schema_for_gemini(cls, schema: Any) -> Any:

        if isinstance(schema, dict):
            new_schema = {}
            for k, v in schema.items():
                if k == "type" and isinstance(v, str):
                    new_schema[k] = v.upper()
                elif k == "format":
                    continue
                else:
                    new_schema[k] = cls._clean_schema_for_gemini(v)
            return new_schema
        elif isinstance(schema, list):
            return [cls._clean_schema_for_gemini(item) for item in schema]
        return schema

    def _convert_tools_to_gemini(self) -> List[Dict[str, Any]]:
        declarations = []
        for tool in ALL_MCP_TOOLS:
            cleaned_schema = self._clean_schema_for_gemini(tool.inputSchema)
            declarations.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": cleaned_schema,
            })
        return [{"function_declarations": declarations}]

    async def _chat_with_gemini(
        self,
        message: str,
        history: List[Dict[str, str]],
        session_id: str,
        current_user_id: Optional[int],
        guest_details: Dict[str, Any],
    ) -> AssistantChatDataSchema:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.gemini_key}"
        
        contents = []
        for turn in history[-6:]:
            role = "user" if turn.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": turn.get("content", "")}]})

        # Augment with current guest details if any
        user_prompt = message
        if guest_details:
            details_str = ", ".join(f"{k}={v}" for k, v in guest_details.items() if v)
            if details_str:
                user_prompt += f"\n[Guest Info Context: {details_str}]"

        contents.append({"role": "user", "parts": [{"text": user_prompt}]})

        gemini_tools = self._convert_tools_to_gemini()
        sys_instruction = await self._build_dynamic_system_instruction()
        payload = {
            "system_instruction": {"parts": [{"text": sys_instruction}]},
            "contents": contents,
            "tools": gemini_tools,
            "tool_config": {
                "function_calling_config": {
                    "mode": "AUTO"
                }
            },
            "generationConfig": {
                "temperature": getattr(settings, "AI_TEMPERATURE", 0.2),
                "maxOutputTokens": getattr(settings, "AI_MAX_TOKENS", 2048),
            },
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()

            candidates = data.get("candidates", [])
            if not candidates:
                return await self._chat_with_intent_fallback(message, history, session_id, current_user_id, guest_details)

            candidate = candidates[0]
            parts = candidate.get("content", {}).get("parts", [])

            # Check for function call
            tool_calls_executed = []
            accumulated_data: Dict[str, Any] = {}
            text_replies = []

            for part in parts:
                if "text" in part:
                    text_replies.append(part["text"])
                elif "functionCall" in part:
                    fn = part["functionCall"]
                    fn_name = fn.get("name")
                    fn_args = fn.get("args") or {}
                    
                    # Merge guest details if provided
                    if guest_details and fn_name in {"checkout_and_book", "register_guest_user"}:
                        for k, v in guest_details.items():
                            if v and k not in fn_args:
                                fn_args[k] = v

                    exec_result = await self.tool_executor.execute_tool(
                        tool_name=fn_name,
                        arguments=fn_args,
                        current_user_id=current_user_id,
                    )

                    tool_calls_executed.append(
                        AssistantToolCallSchema(
                            tool=fn_name,
                            arguments=fn_args,
                            result=exec_result.data or (exec_result.content[0].text if exec_result.content else None),
                            is_error=exec_result.isError,
                        )
                    )

                    if exec_result.data:
                        if fn_name in {"search_homestays", "semantic_search_homestays"}:
                            accumulated_data["search_results"] = exec_result.data.get("properties")
                        elif fn_name == "check_stay_availability":
                            accumulated_data["availability"] = exec_result.data
                        elif fn_name == "checkout_and_book":
                            accumulated_data["booking"] = exec_result.data
                        elif fn_name == "register_guest_user":
                            accumulated_data["user"] = exec_result.data

                    # Send function response back to Gemini for natural reply
                    tool_text = exec_result.content[0].text if exec_result.content else "Done"
                    follow_up_contents = list(contents)
                    follow_up_contents.append({"role": "model", "parts": [part]})
                    follow_up_contents.append({
                        "role": "function",
                        "parts": [{"functionResponse": {"name": fn_name, "response": {"result": tool_text}}}],
                    })

                    follow_payload = {
                        "system_instruction": {"parts": [{"text": sys_instruction}]},
                        "contents": follow_up_contents,
                    }

                    follow_resp = await client.post(url, json=follow_payload)
                    if follow_resp.status_code == 200:
                        f_data = follow_resp.json()
                        f_candidates = f_data.get("candidates", [])
                        if f_candidates:
                            f_parts = f_candidates[0].get("content", {}).get("parts", [])
                            text_replies = [p["text"] for p in f_parts if "text" in p]

            raw_reply = " ".join(text_replies).strip()
            final_reply = await self._enrich_reply(
                reply=raw_reply,
                tool_calls=tool_calls_executed,
                accumulated_data=accumulated_data,
                user_message=message,
            )

        suggested_actions = self._generate_suggestions(tool_calls_executed, accumulated_data)

        return AssistantChatDataSchema(
            reply=final_reply,
            session_id=session_id,
            intent=tool_calls_executed[0].tool if tool_calls_executed else ("greeting" if ('is_pure_greeting' in locals() and is_pure_greeting) else "general_chat"),
            action_taken=f"Executed {len(tool_calls_executed)} tool(s)" if tool_calls_executed else None,
            tool_calls=tool_calls_executed,
            search_results=accumulated_data.get("search_results"),
            availability=accumulated_data.get("availability"),
            booking=accumulated_data.get("booking"),
            user=accumulated_data.get("user"),
            suggested_actions=suggested_actions,
        )


    # --------------------------------------------------------------------------
    # OpenAI REST Client with Tool Calling
    # --------------------------------------------------------------------------

    def _convert_tools_to_openai(self) -> List[Dict[str, Any]]:
        tools = []
        for t in ALL_MCP_TOOLS:
            tools.append({
                "type": "function",
                "function": {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.inputSchema,
                }
            })
        return tools

    async def _chat_with_openai(
        self,
        message: str,
        history: List[Dict[str, str]],
        session_id: str,
        current_user_id: Optional[int],
        guest_details: Dict[str, Any],
    ) -> AssistantChatDataSchema:
        """Execute chat turn using OpenAI Chat Completions API with function calling."""
        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.openai_key}",
            "Content-Type": "application/json",
        }

        sys_instruction = await self._build_dynamic_system_instruction()
        messages = [{"role": "system", "content": sys_instruction}]
        for turn in history[-6:]:
            messages.append({"role": turn.get("role", "user"), "content": turn.get("content", "")})

        user_prompt = message
        if guest_details:
            details_str = ", ".join(f"{k}={v}" for k, v in guest_details.items() if v)
            if details_str:
                user_prompt += f"\n[Guest Info Context: {details_str}]"

        messages.append({"role": "user", "content": user_prompt})

        payload = {
            "model": self.model if "gpt" in self.model else "gpt-4o-mini",
            "messages": messages,
            "tools": self._convert_tools_to_openai(),
            "tool_choice": "auto",
            "temperature": getattr(settings, "AI_TEMPERATURE", 0.2),
        }

        tool_calls_executed = []
        accumulated_data: Dict[str, Any] = {}
        final_reply = ""

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()

            choice = data.get("choices", [{}])[0]
            assistant_msg = choice.get("message", {})

            if "tool_calls" in assistant_msg and assistant_msg["tool_calls"]:
                messages.append(assistant_msg)
                for tc in assistant_msg["tool_calls"]:
                    fn = tc.get("function", {})
                    fn_name = fn.get("name")
                    fn_args = json.loads(fn.get("arguments", "{}"))

                    if guest_details and fn_name in {"checkout_and_book", "register_guest_user"}:
                        for k, v in guest_details.items():
                            if v and k not in fn_args:
                                fn_args[k] = v

                    exec_result = await self.tool_executor.execute_tool(
                        tool_name=fn_name,
                        arguments=fn_args,
                        current_user_id=current_user_id,
                    )

                    tool_calls_executed.append(
                        AssistantToolCallSchema(
                            tool=fn_name,
                            arguments=fn_args,
                            result=exec_result.data or (exec_result.content[0].text if exec_result.content else None),
                            is_error=exec_result.isError,
                        )
                    )

                    if exec_result.data:
                        if fn_name in {"search_homestays", "semantic_search_homestays"}:
                            accumulated_data["search_results"] = exec_result.data.get("properties")
                        elif fn_name == "check_stay_availability":
                            accumulated_data["availability"] = exec_result.data
                        elif fn_name == "checkout_and_book":
                            accumulated_data["booking"] = exec_result.data
                        elif fn_name == "register_guest_user":
                            accumulated_data["user"] = exec_result.data

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.get("id"),
                        "content": exec_result.content[0].text if exec_result.content else "{}",
                    })

                follow_payload = {
                    "model": payload["model"],
                    "messages": messages,
                }
                follow_resp = await client.post(url, headers=headers, json=follow_payload)
                if follow_resp.status_code == 200:
                    f_data = follow_resp.json()
                    f_choice = f_data.get("choices", [{}])[0]
                    final_reply = f_choice.get("message", {}).get("content", "")
            else:
                final_reply = assistant_msg.get("content", "")

        if not tool_calls_executed:
            msg_l = message.lower()
            is_actionable = any(w in msg_l for w in ["find", "search", "stay", "homestay", "room", "book", "reserve", "availability", "price", "quote", "status", "cancel", "where", "destination"])
            is_pure_greeting = any(g in msg_l for g in ["hi", "hello", "hey", "who are you"]) and not is_actionable
            if is_actionable and not is_pure_greeting:
                return await self._chat_with_intent_fallback(message, history, session_id, current_user_id, guest_details)

        final_reply = await self._enrich_reply(final_reply, tool_calls_executed, accumulated_data, message)
        suggested_actions = self._generate_suggestions(tool_calls_executed, accumulated_data)

        return AssistantChatDataSchema(
            reply=final_reply,
            session_id=session_id,
            intent=tool_calls_executed[0].tool if tool_calls_executed else ("greeting" if ('is_pure_greeting' in locals() and is_pure_greeting) else "general_chat"),
            action_taken=f"Executed {len(tool_calls_executed)} tool(s)" if tool_calls_executed else None,
            tool_calls=tool_calls_executed,
            search_results=accumulated_data.get("search_results"),
            availability=accumulated_data.get("availability"),
            booking=accumulated_data.get("booking"),
            user=accumulated_data.get("user"),
            suggested_actions=suggested_actions,
        )

    # --------------------------------------------------------------------------
    # Amazon Bedrock Nova Lite Client with Converse API & Tool Calling
    # --------------------------------------------------------------------------

    def _convert_tools_to_bedrock(self) -> List[Dict[str, Any]]:
        """Convert MCP tool definitions into Amazon Bedrock Converse toolSpec objects."""
        tools = []
        for t in ALL_MCP_TOOLS:
            tools.append({
                "toolSpec": {
                    "name": t.name,
                    "description": t.description,
                    "inputSchema": {
                        "json": t.inputSchema
                    }
                }
            })
        return tools

    async def _chat_with_bedrock(
        self,
        message: str,
        history: List[Dict[str, str]],
        session_id: str,
        current_user_id: Optional[int],
        guest_details: Dict[str, Any],
    ) -> AssistantChatDataSchema:
        """Execute chat turn using Amazon Bedrock Nova Lite via Converse API with tool execution."""
        sys_instruction = await self._build_dynamic_system_instruction()

        bedrock_messages = []
        for turn in history[-6:]:
            role = "user" if turn.get("role") == "user" else "assistant"
            bedrock_messages.append({"role": role, "content": [{"text": turn.get("content", "")}]})

        user_prompt = message
        if guest_details:
            details_str = ", ".join(f"{k}={v}" for k, v in guest_details.items() if v)
            if details_str:
                user_prompt += f"\n[Guest Info Context: {details_str}]"

        bedrock_messages.append({"role": "user", "content": [{"text": user_prompt}]})

        model_id = self.model or getattr(settings, "BEDROCK_NOVA_MODEL_ID", "amazon.nova-lite-v1:0")
        tool_config = {"tools": self._convert_tools_to_bedrock()}

        def _invoke_converse(msgs: List[Dict[str, Any]], tools: Optional[Dict[str, Any]] = None):
            client = self._get_bedrock_client()
            kwargs: Dict[str, Any] = {
                "modelId": model_id,
                "messages": msgs,
                "system": [{"text": sys_instruction}],
                "inferenceConfig": {
                    "maxTokens": getattr(settings, "AI_MAX_TOKENS", 2048),
                    "temperature": getattr(settings, "AI_TEMPERATURE", 0.2),
                },
            }
            if tools and "tools" in tools and tools["tools"]:
                kwargs["toolConfig"] = tools
            return client.converse(**kwargs)

        response = await asyncio.to_thread(_invoke_converse, bedrock_messages, tool_config)
        output_msg = response.get("output", {}).get("message", {})
        stop_reason = response.get("stopReason")

        tool_calls_executed = []
        accumulated_data: Dict[str, Any] = {}
        final_reply = ""

        # Extract tool use blocks if any
        content_blocks = output_msg.get("content", [])
        tool_use_blocks = [blk["toolUse"] for blk in content_blocks if isinstance(blk, dict) and "toolUse" in blk]

        if stop_reason == "tool_use" or tool_use_blocks:
            bedrock_messages.append(output_msg)
            tool_result_content = []

            for tu in tool_use_blocks:
                fn_name = tu.get("name")
                fn_args = tu.get("input") or {}
                tool_use_id = tu.get("toolUseId")

                if guest_details and fn_name in {"checkout_and_book", "register_guest_user"}:
                    for k, v in guest_details.items():
                        if v and k not in fn_args:
                            fn_args[k] = v

                exec_result = await self.tool_executor.execute_tool(
                    tool_name=fn_name,
                    arguments=fn_args,
                    current_user_id=current_user_id,
                )

                tool_calls_executed.append(
                    AssistantToolCallSchema(
                        tool=fn_name,
                        arguments=fn_args,
                        result=exec_result.data or (exec_result.content[0].text if exec_result.content else None),
                        is_error=exec_result.isError,
                    )
                )

                if exec_result.data:
                    if fn_name in {"search_homestays", "semantic_search_homestays"}:
                        accumulated_data["search_results"] = exec_result.data.get("properties")
                    elif fn_name == "check_stay_availability":
                        accumulated_data["availability"] = exec_result.data
                    elif fn_name == "checkout_and_book":
                        accumulated_data["booking"] = exec_result.data
                    elif fn_name == "register_guest_user":
                        accumulated_data["user"] = exec_result.data

                result_text = exec_result.content[0].text if exec_result.content else "{}"
                tool_result_content.append({
                    "toolResult": {
                        "toolUseId": tool_use_id,
                        "content": [{"text": result_text}],
                        "status": "error" if exec_result.isError else "success",
                    }
                })

            bedrock_messages.append({"role": "user", "content": tool_result_content})

            # Send tool results back to Bedrock for final natural language response
            follow_response = await asyncio.to_thread(_invoke_converse, bedrock_messages, None)
            follow_msg = follow_response.get("output", {}).get("message", {})
            f_blocks = follow_msg.get("content", [])
            text_pieces = [b["text"] for b in f_blocks if isinstance(b, dict) and "text" in b]
            final_reply = " ".join(text_pieces).strip()
        else:
            text_pieces = [b["text"] for b in content_blocks if isinstance(b, dict) and "text" in b]
            final_reply = " ".join(text_pieces).strip()

        if not tool_calls_executed:
            msg_l = message.lower()
            is_actionable = any(w in msg_l for w in ["find", "search", "stay", "homestay", "room", "book", "reserve", "availability", "price", "quote", "status", "cancel", "where", "destination"])
            is_pure_greeting = any(g in msg_l for g in ["hi", "hello", "hey", "who are you"]) and not is_actionable
            if is_actionable and not is_pure_greeting:
                return await self._chat_with_intent_fallback(message, history, session_id, current_user_id, guest_details)

        final_reply = await self._enrich_reply(final_reply, tool_calls_executed, accumulated_data, message)
        suggested_actions = self._generate_suggestions(tool_calls_executed, accumulated_data)

        return AssistantChatDataSchema(
            reply=final_reply,
            session_id=session_id,
            intent=tool_calls_executed[0].tool if tool_calls_executed else ("greeting" if ('is_pure_greeting' in locals() and is_pure_greeting) else "general_chat"),
            action_taken=f"Executed {len(tool_calls_executed)} tool(s)" if tool_calls_executed else None,
            tool_calls=tool_calls_executed,
            search_results=accumulated_data.get("search_results"),
            availability=accumulated_data.get("availability"),
            booking=accumulated_data.get("booking"),
            user=accumulated_data.get("user"),
            suggested_actions=suggested_actions,
        )

    async def _resolve_dynamic_context(self) -> Dict[str, Any]:
        """Resolve platform name, active country, and active cities/locations from settings & DB."""
        app_name = "TashiHome"
        country_name = ""
        if hasattr(self.tool_executor, "setting_service") and self.tool_executor.setting_service:
            try:
                name_val = await self.tool_executor.setting_service.get_value("app_name") or await self.tool_executor.setting_service.get_value("site_name")
                if name_val:
                    app_name = str(name_val).strip()
            except Exception:
                pass

        if hasattr(self.tool_executor, "_resolve_platform_country"):
            try:
                country_name = await self.tool_executor._resolve_platform_country() or ""
            except Exception:
                pass

        cities_map: Dict[str, str] = {}
        if hasattr(self.tool_executor, "_get_active_cities_map"):
            try:
                cities_map = await self.tool_executor._get_active_cities_map()
            except Exception:
                pass

        locations_map: Dict[str, str] = {}
        if hasattr(self.tool_executor, "_get_active_locations_map"):
            try:
                locations_map = await self.tool_executor._get_active_locations_map()
            except Exception:
                pass

        city_names = list(dict.fromkeys(cities_map.values()))
        loc_names = list(dict.fromkeys(locations_map.values()))

        date_format_pattern = "YYYY-MM-DD"
        if hasattr(self.tool_executor, "_get_date_format_pattern"):
            try:
                date_format_pattern = await self.tool_executor._get_date_format_pattern() or "YYYY-MM-DD"
            except Exception:
                pass

        today = date.today()
        example_cin = today + timedelta(days=7)
        example_cout = today + timedelta(days=10)
        date_format_example = "YYYY-MM-DD"
        if hasattr(self.tool_executor, "_format_date_with_pattern"):
            date_format_example = f"{self.tool_executor._format_date_with_pattern(example_cin, date_format_pattern)} to {self.tool_executor._format_date_with_pattern(example_cout, date_format_pattern)}"
        else:
            date_format_example = f"{example_cin.isoformat()} to {example_cout.isoformat()}"

        default_currency = "INR"
        currency_symbol = "₹"
        if hasattr(self.tool_executor, "_resolve_currency_and_symbol"):
            try:
                default_currency, currency_symbol = await self.tool_executor._resolve_currency_and_symbol()
            except Exception:
                pass

        return {
            "app_name": app_name,
            "country_name": country_name,
            "default_currency": default_currency,
            "currency_symbol": currency_symbol,
            "cities_map": cities_map,
            "locations_map": locations_map,
            "city_names": city_names,
            "location_names": loc_names,
            "date_format_pattern": date_format_pattern,
            "date_format_example": date_format_example,
        }

    async def _build_dynamic_system_instruction(self) -> str:
        """Build setting-driven, country-aware, and date-format-aware system instructions."""
        if settings.AI_SYSTEM_INSTRUCTION:
            return settings.AI_SYSTEM_INSTRUCTION

        ctx = await self._resolve_dynamic_context()
        app_name = ctx["app_name"] or "TashiHome"
        country_name = ctx["country_name"] or ""
        country_ref = f" in {country_name}" if country_name else ""
        date_fmt = ctx["date_format_pattern"] or "YYYY-MM-DD"
        date_example = ctx["date_format_example"] or "2026-10-01 to 2026-10-05"
        cities_str = ", ".join(ctx["city_names"][:5]) if ctx["city_names"] else "popular destinations"
        curr_sym = ctx.get("currency_symbol") or "₹"
        curr_code = ctx.get("default_currency") or "INR"

        return f"""You are the AI Travel Concierge for {app_name} (the premier homestay booking platform{country_ref}).

CRITICAL INSTRUCTIONS FOR TOOL EXECUTION & RESPONSE FORMATTING:
1. ALWAYS use the `search_homestays` or `semantic_search_homestays` tool whenever a user asks to search, find, or explore homestays, accommodations, rooms, or destinations.
   - You can search by destination/city ({cities_str}), specific location/neighborhood, or street address.
   - Always invoke a search tool first to query the live database.
2. WHEN HOMESTAYS ARE RETURNED:
   - Provide a warm, well-formatted response listing each homestay with:
     * Name, city, specific location/neighborhood, and address
     * Nightly rate with setting-driven currency symbol (e.g. {curr_sym} / {curr_code})
     * Rating and key features/amenities
   - Prompt the user to check availability for specific dates ({date_fmt}) or proceed with booking.
3. WHEN 0 HOMESTAYS ARE FOUND (e.g. non-served locations or unavailable dates):
   - Explicitly state that 0 matching homestays were found for that location.
   - Suggest exploring available featured destinations and cities ({cities_str}) from our platform listings.
4. DATE HANDLING & CAPACITY-BASED OCCUPANCY PRICING FOR AVAILABILITY & BOOKING:
   - Each homestay offers specific room types with capacity-based variable pricing tiers.
   - When presenting room types or answering inquiries about rates/availability, ALWAYS list the room type along with its maximum capacity and the full breakdown of occupancy-wise rates.
   - When checking availability or calculating quotes, highlight the active guest occupancy tier applied.
   - If a user asks to check availability or checkout/book without specifying dates or room type, query the property details, present available room types with full occupancy pricing tiers, and politely ASK the user for:
     1. Check-in & Check-out dates in {date_fmt} format (e.g. {date_example})
     2. Number of guests and rooms
     3. Preferred Room Type
    - DO NOT hallucinate, fabricate, or pick past or arbitrary dates.
5. CHECKOUT & PAYMENT HANDLING:
   - If online payment is ENABLED: after checkout completes, present the booking reference, homestay name, total amount, and direct payment gateway details (Order ID and payment link).
   - If online payment is DISABLED: inform the guest that online booking creation is currently disabled because payment processing is turned off by platform configuration.
6. INITIATE PAYMENT & BOOKING REFERENCE LOOKUP:
   - If a guest asks how to pay for an existing booking, asks for a payment link, or provides a reservation reference (e.g. 'Pay for BK-XXXX' or 'Generate payment link'), call `initiate_booking_payment`. If payments are disabled, inform them to pay on arrival.
   - If a guest asks to search, track, or check status of any booking reference (e.g. BK-XXXX, BKXXXX, or reference code), call `get_booking_status`.
7. If a guest asks to cancel, call `cancel_booking`.
8. If a guest asks about popular destinations, call `get_popular_destinations`.
9. Tone: Warm, respectful, authentic hospitality (Tashi Delek!), concise, helpful, and transparent. NEVER reply with just a generic one-liner like "Here is what I found for you."
"""

    async def _enrich_reply(
        self,
        reply: str,
        tool_calls: List[AssistantToolCallSchema],
        accumulated_data: Dict[str, Any],
        user_message: str,
    ) -> str:
        reply_clean = (reply or "").strip()
        terse_replies = {
            "", "done", "here is what i found for you.", "here is what i found for you",
            "here's what i found for you.", "here's what i found for you",
            "i have completed your request on tashihome.", "i have processed your request for tashihome."
        }

        ctx = await self._resolve_dynamic_context()
        app_name = ctx["app_name"]
        country_name = ctx["country_name"]

        # If search tool was executed, construct informative response
        search_tools = [tc for tc in tool_calls if tc.tool in {"search_homestays", "semantic_search_homestays"}]
        if search_tools:
            props = accumulated_data.get("search_results") or []
            search_arg = (search_tools[0].arguments or {}).get("query") or user_message
            clean_dest = re.sub(r"\b(find|search|show|look\s+for|explore|compare|comparison|other|another|different|various|options?|alternatives?|similar|view|browse|list|all|available|homestays?|homstays?|stays?|rooms?|in|at|near|for|me|please)\b", "", search_arg, flags=re.IGNORECASE).strip().title()
            dest_label = clean_dest if clean_dest and clean_dest.lower() not in {"all", "any", "everywhere", "compare", "other", "compare other", "options", "another", "different", country_name.lower()} else (country_name or "our destinations")

            if props:
                if len(reply_clean) > 60 and reply_clean.lower() not in terse_replies:
                    return reply_clean
                formatted = f"Kuzu Zangpo La! 🙏 I found **{len(props)} homestay(s)** in {dest_label}:\n\n"
                for i, p in enumerate(props[:4], 1):
                    name = p.get("name") or "Homestay"
                    city = p.get("city") or p.get("city_name") or dest_label
                    price = p.get("base_price") or p.get("price_per_night") or "Contact for price"
                    currency_sym = p.get("currency_symbol") or p.get("currency") or ctx.get("currency_symbol") or "₹"
                    rating_val = p.get("rating")
                    reviews = p.get("review_count") or 0
                    rating_str = f"⭐ {rating_val} ({reviews} reviews)" if (rating_val is not None and float(rating_val) > 0) or reviews > 0 else "⭐ New (No reviews yet)"
                    prop_type = p.get("property_type") or p.get("type") or "Homestay"
                    match_pct = p.get("match_percentage")
                    match_badge = f" | ✨ {match_pct}% match" if match_pct else ""

                    formatted += f"**{i}. {name}** ({city})\n"
                    formatted += f"   • Price: {currency_sym} {price}/night | Rating: {rating_str}{match_badge}\n"
                    formatted += f"   • Type: {prop_type}\n\n"
                formatted += "Would you like to check availability dates or book one of these homestays?"
                return formatted
            else:
                cities_display = ", ".join([f"**{c}**" for c in ctx["city_names"][:3]]) if ctx["city_names"] else "our featured destinations"
                country_ref = f" in {country_name}" if country_name else ""
                return (
                    f"Kuzu Zangpo La! 🙏 I searched for homestays in **{dest_label}**, but we currently do not have matching listings in that location.\n\n"
                    f"{app_name} specializes in authentic homestays{country_ref} across destinations like {cities_display}.\n\n"
                    f"Would you like to explore homestays in one of these regions?"
                )

        # If the reply is already long and detailed, keep it
        if len(reply_clean) > 60 and reply_clean.lower() not in terse_replies:
            return reply_clean

        return reply_clean or f"I have processed your request for {app_name}. How else may I assist you?"



    @staticmethod
    def _format_room_types_summary(room_types: List[Dict[str, Any]], curr_sym: str, default_base_price: float = 0.0) -> str:
        if not room_types:
            return f"• Standard Rate: {curr_sym} {default_base_price}/night"
        rt_lines = []
        for rt in room_types:
            name = rt.get("name", "Standard Room")
            cap = rt.get("capacity", 2)
            base_p = rt.get("price_per_night", rt.get("base_price", 0.0))
            tiers = rt.get("pricing_tiers") or []
            if tiers:
                tier_strs = [f"{t.get('occupancy')} Guests: {curr_sym} {float(t.get('price_per_night', t.get('base_price', 0.0))):,.0f}" for t in sorted(tiers, key=lambda x: x.get('occupancy', 0))]
                rt_lines.append(
                    f"• **{name}** (Up to {cap} guests)\n"
                    f"  └ **Room Rates by Occupancy**: {' | '.join(tier_strs)}"
                )
            else:
                rt_lines.append(f"• **{name}**: {curr_sym} {base_p}/night (Up to {cap} guests)")
        return "\n".join(rt_lines)

    # --------------------------------------------------------------------------
    # Deterministic NLP / Intent Engine Fallback
    # --------------------------------------------------------------------------

    async def _chat_with_intent_fallback(
        self,
        message: str,
        history: List[Dict[str, str]],
        session_id: str,
        current_user_id: Optional[int],
        guest_details: Dict[str, Any],
    ) -> AssistantChatDataSchema:
        """Intelligent rule and regex based NLP engine for parsing search, checkout, registration, and status."""
        msg_lower = message.lower().strip()
        tool_calls: List[AssistantToolCallSchema] = []
        accumulated_data: Dict[str, Any] = {}
        reply = ""

        ctx = await self._resolve_dynamic_context()
        app_name = ctx["app_name"]
        country_name = ctx["country_name"]
        cities_map = ctx["cities_map"]
        locations_map = ctx["locations_map"]
        city_names = ctx["city_names"]

        date_fmt = ctx.get("date_format_pattern", "YYYY-MM-DD")
        date_example = ctx.get("date_format_example", "2026-10-01 to 2026-10-05")

        # Extract dates if present (YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, YYYY/MM/DD, etc.)
        parsed_dates: List[str] = []
        raw_date_matches = re.findall(
            r"\b(\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{1,2}[-/]\d{1,2}[-/]\d{4})\b",
            message
        )
        for dm in raw_date_matches:
            if hasattr(self.tool_executor, "_parse_date"):
                d_obj = self.tool_executor._parse_date(dm)
                if d_obj:
                    parsed_dates.append(d_obj.isoformat())
            else:
                parsed_dates.append(dm)

        date_matches = parsed_dates
        cin = date_matches[0] if len(date_matches) >= 1 else (date.today() + timedelta(days=7)).isoformat()
        cout = date_matches[1] if len(date_matches) >= 2 else (date.today() + timedelta(days=9)).isoformat()

        # Extract booking reference or invoice reference (e.g. BK-2026-XXXX, BK260908AB12, INV-2026-0001, or UUID)
        ref_match = re.search(r"\b(bk-?[0-9a-zA-Z_-]+|inv-?[0-9a-zA-Z_-]+)\b", message, flags=re.IGNORECASE)
        found_ref = ref_match.group(1).upper() if ref_match else ""

        # Extract room type keyword (e.g. Deluxe, Standard, Suite, Family Room, Cottage, Single, Double)
        room_type_target: Optional[str] = None
        rt_match = re.search(r"\b(deluxe(?:\s+room)?|standard(?:\s+room)?|suite|cottage|family(?:\s+room)?|single(?:\s+room)?|double(?:\s+room)?|executive(?:\s+room)?|superior(?:\s+room)?)\b", message, flags=re.IGNORECASE)
        if rt_match:
            room_type_target = rt_match.group(1).strip()

        # Extract guest count
        guests_match = re.search(r"(\d+)\s*(?:guest|people|person|adult)", msg_lower)
        num_guests = int(guests_match.group(1)) if guests_match else 1

        # Extract rooms count
        rooms_match = re.search(r"(\d+)\s*(?:room)", msg_lower)
        num_rooms = int(rooms_match.group(1)) if rooms_match else 1

        # Extract email
        email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", message)
        guest_email = email_match.group(0) if email_match else guest_details.get("guest_email")

        # Extract phone
        phone_match = re.search(r"(\+?[0-9]{8,15})", message)
        guest_phone = phone_match.group(0) if phone_match else guest_details.get("guest_phone")

        ignored_names = {
            "all", "any", "everywhere", "compare", "other", "compare other", "options",
            "another", "different", "various", "alternatives", "similar", "view",
            "browse", "list", "homestay", "homestays", "property", "properties", "stays", "rooms", "hotels"
        }
        if country_name:
            ignored_names.add(country_name.lower())
        ignored_names.update(cities_map.keys())
        ignored_names.update(locations_map.keys())

        # Extract property identifier (UUID, parenthesized slug, quoted name, or keyword)
        prop_target: Optional[str] = None
        uuid_match = re.search(r"\b([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\b", message)
        if uuid_match:
            prop_target = uuid_match.group(1)

        if not prop_target:
            paren_match = re.search(r"\(([a-zA-Z0-9_-]+)\)", message)
            if paren_match:
                candidate = paren_match.group(1).strip()
                if candidate.lower() not in ignored_names:
                    prop_target = candidate

        if not prop_target:
            quote_match = re.search(r'["\']([^"\']+)["\']', message)
            if quote_match:
                candidate = quote_match.group(1).strip()
                if candidate:
                    prop_target = candidate

        if not prop_target:
            prop_phrase_match = re.search(
                r"(?:checkout|book|reserve|availability\s+(?:and\s+price\s+quote\s+)?(?:of|for|at)\s+|for\s+homestay\s+|at\s+homestay\s+|for\s+stay\s+|at\s+stay\s+)([\w\s-]+?)(?:\s+from|\s+on|\s+for\s+\d+|\s+between|$)",
                message,
                flags=re.IGNORECASE,
            )
            if prop_phrase_match:
                candidate = prop_phrase_match.group(1).strip()
                if candidate and candidate.lower() not in ignored_names:
                    prop_target = candidate

        # 1. Booking Status / Reference Search Intent
        is_ref_status = (
            (found_ref != "" and not any(k in msg_lower for k in ["pay", "payment", "cancel", "checkout", "book"]))
            or (any(k in msg_lower for k in ["booking status", "track booking", "track reservation", "check booking", "search booking", "booking reference", "reference status", "check status", "my booking", "my reservation", "find booking", "reservation status"]))
            or ("reference" in msg_lower and any(k in msg_lower for k in ["search", "find", "status", "check", "lookup", "track", "where", "show"]))
        ) and not any(k in msg_lower for k in ["pay", "payment", "razorpay", "pay now", "cancel"])

        if is_ref_status:
            booking_ref = found_ref or (uuid_match.group(1) if uuid_match else "")
            if booking_ref:
                res = await self.tool_executor.execute_tool("get_booking_status", {"booking_reference": booking_ref}, current_user_id)
                tool_calls.append(AssistantToolCallSchema(tool="get_booking_status", arguments={"booking_reference": booking_ref}, result=res.data, is_error=res.isError))
                if not res.isError and res.data:
                    accumulated_data["booking"] = res.data
                    fmt_cin = res.data.get("formatted_check_in_date") or res.data.get("check_in_date")
                    fmt_cout = res.data.get("formatted_check_out_date") or res.data.get("check_out_date")
                    curr_sym = res.data.get("currency_symbol") or res.data.get("currency") or ctx.get("currency_symbol") or "₹"
                    reply = (
                        f"Here are the details for reservation **{res.data['booking_reference']}**:\n"
                        f"- Property: {res.data['property_name']}\n"
                        f"- Status: {res.data['status']}\n"
                        f"- Payment: {res.data['payment_status']}\n"
                        f"- Dates: {fmt_cin} to {fmt_cout}\n"
                        f"- Guests & Rooms: {res.data.get('num_guests', 1)} guest(s), {res.data.get('num_rooms', 1)} room(s)\n"
                        f"- Total: {curr_sym} {res.data['total_amount']}"
                    )
                else:
                    reply = f"I couldn't find an active reservation for reference '{booking_ref}'. Please verify the reference code (e.g., BK-2026-XXXX or BK260908AB12)."
            else:
                reply = "Please provide your booking reference code (e.g. BK-XXXX or BK260908AB12) to check your reservation status."
            intent_name = "get_booking_status"

        # 1b. Payment Gateway & Pay Now Intent
        elif any(k in msg_lower for k in ["pay", "payment", "razorpay", "pay now", "payment link", "pay booking", "checkout link"]):
            if not settings.PAYMENT_ENABLED:
                reply = (
                    "ℹ️ **Online Payments Disabled**: Online payment processing is currently disabled by platform configuration. "
                    "You can complete your payment directly at the homestay upon arrival."
                )
                intent_name = "initiate_booking_payment"
            else:
                booking_ref = found_ref or (uuid_match.group(1) if uuid_match else "")
                if booking_ref:
                    res = await self.tool_executor.execute_tool("initiate_booking_payment", {"booking_reference": booking_ref}, current_user_id)
                    tool_calls.append(AssistantToolCallSchema(tool="initiate_booking_payment", arguments={"booking_reference": booking_ref}, result=res.data, is_error=res.isError))
                    if not res.isError and res.data:
                        accumulated_data["payment"] = res.data
                        gw = res.data.get("payment_gateway") or {}
                        prop_title = res.data.get("property_name") or "Homestay Reservation"
                        curr_sym = gw.get("currency_symbol") or res.data.get("currency_symbol") or gw.get("currency") or ctx.get("currency_symbol") or "₹"
                        reply = (
                            f"💳 **Payment Gateway Session for {res.data['booking_reference']}**\n\n"
                            f"• **Homestay**: {prop_title}\n"
                            f"• **Amount Due**: {curr_sym} {gw.get('amount', res.data.get('total_amount'))}\n"
                            f"• **Gateway Order ID**: `{gw.get('order_id')}`\n"
                            f"• **Payment Link**: [Complete Payment Online]({gw.get('payment_url')})\n\n"
                            f"You can complete your payment securely using Credit/Debit Cards, UPI, or Netbanking."
                        )
                    else:
                        reply = f"Could not generate payment gateway session: {res.content[0].text if res.content else 'Please verify your booking reference.'}"
                    intent_name = "initiate_booking_payment"
                else:
                    reply = "Please provide your booking reference code (e.g. BK-XXXX or BK260908AB12) to generate your secure payment gateway link."
                    intent_name = "initiate_booking_payment"

        # 2. Cancellation Intent
        elif "cancel" in msg_lower and any(k in msg_lower for k in ["booking", "reservation", "stay"]):
            booking_ref = found_ref or (uuid_match.group(1) if uuid_match else "")
            if booking_ref:
                res = await self.tool_executor.execute_tool("cancel_booking", {"booking_reference": booking_ref, "reason": "Cancelled via Assistant"}, current_user_id)
                tool_calls.append(AssistantToolCallSchema(tool="cancel_booking", arguments={"booking_reference": booking_ref}, result=res.data, is_error=res.isError))
                reply = f"Your booking **{booking_ref}** has been cancelled. If eligible, refund processing will follow the property's cancellation policy."
            else:
                reply = "Please provide the booking reference code (e.g. BK-XXXX or BK260908AB12) you would like to cancel."
            intent_name = "cancel_booking"
        # 3. Checkout / Booking Creation Intent
        elif any(k in msg_lower for k in ["book", "reserve", "checkout", "confirm booking"]):
            if not settings.PAYMENT_ENABLED:
                reply = (
                    "ℹ️ **Online Booking & Payments Disabled**: Booking creation is currently disabled because payment processing is turned off by platform configuration. "
                    "Reservations cannot be created at this time."
                )
                intent_name = "checkout_and_book"
            else:
                selected_prop = prop_target
                if not selected_prop:
                    for key, val in cities_map.items():
                        if key in msg_lower:
                            selected_prop = val
                            break
                
                if not selected_prop:
                    search_res = await self.tool_executor.execute_tool("search_homestays", {"query": "", "page_size": 1}, current_user_id)
                    props = (search_res.data or {}).get("properties", [])
                    selected_prop = props[0]["slug"] if props else None

                if not selected_prop:
                    selected_prop = "homestay"

                # If user hasn't provided check-in and check-out dates, fetch homestay room types and prompt user
                if len(date_matches) < 2:
                    details_res = await self.tool_executor.execute_tool("get_homestay_details", {"property_id": selected_prop}, current_user_id)
                    tool_calls.append(AssistantToolCallSchema(tool="get_homestay_details", arguments={"property_id": selected_prop}, result=details_res.data, is_error=details_res.isError))
                    
                    prop_name = (details_res.data or {}).get("name", selected_prop)
                    currency = (details_res.data or {}).get("currency") or ctx.get("default_currency", "INR")
                    curr_sym = (details_res.data or {}).get("currency_symbol") or ctx.get("currency_symbol", "₹")
                    room_types = (details_res.data or {}).get("room_types", [])
                    raw_base_price = (details_res.data or {}).get("base_price", 0.0)
                    base_price = float(raw_base_price) if raw_base_price is not None else 0.0

                    accumulated_data["homestay"] = details_res.data
                    max_g = (details_res.data or {}).get("max_guests") or 2
                    max_r = (details_res.data or {}).get("max_rooms") or 1
                    tot_u = (details_res.data or {}).get("total_units") or max_r
                    cap_v = (details_res.data or {}).get("capacity") or max_g
                    accumulated_data["availability"] = {
                        "property_name": prop_name,
                        "property_slug": (details_res.data or {}).get("slug", selected_prop),
                        "currency": currency,
                        "currency_symbol": curr_sym,
                        "room_types": room_types,
                        "max_guests": max_g,
                        "max_rooms": max_r,
                        "total_units": tot_u,
                        "capacity": cap_v,
                        "is_available": True,
                        "price_per_night": base_price,
                        "subtotal": base_price,
                        "tax_amount": 0.0,
                        "total_amount": base_price,
                        "requires_dates": True,
                    }

                    rt_section = self._format_room_types_summary(room_types, curr_sym, base_price)

                    reply = (
                        f"To complete your checkout for **{prop_name}**, please select your dates, room count, and preferred room type:\n\n"
                        f"**Available Room Types & Room-Wise Rates:**\n"
                        f"{rt_section}\n\n"
                        f"Please provide:\n"
                        f"1. 📅 **Check-in & Check-out dates** ({date_fmt}, e.g. {date_example})\n"
                        f"2. 👥 **Number of guests & rooms**\n"
                        f"3. 🛏️ **Preferred Room Type**\n\n"
                        f"Once confirmed, I will calculate the exact quote and generate your secure payment gateway link!"
                    )
                    intent_name = "checkout_and_book"
                else:
                    # Auto-extract or default guest info
                    g_name = guest_details.get("guest_name") or "Guest Traveler"
                    g_email = guest_email or "guest@tashihomes.in"
                    g_phone = guest_phone or "+97517123456"

                    checkout_args = {
                        "property_id": selected_prop,
                        "check_in_date": cin,
                        "check_out_date": cout,
                        "num_guests": num_guests,
                        "num_rooms": num_rooms,
                        "room_type_id": room_type_target,
                        "guest_name": g_name,
                        "guest_email": g_email,
                        "guest_phone": g_phone,
                    }

                    res = await self.tool_executor.execute_tool("checkout_and_book", checkout_args, current_user_id)
                    tool_calls.append(AssistantToolCallSchema(tool="checkout_and_book", arguments=checkout_args, result=res.data, is_error=res.isError))

                    if not res.isError and res.data:
                        accumulated_data["booking"] = res.data
                        gw = res.data.get("payment_gateway") or {}
                        curr_sym = res.data.get("currency_symbol") or res.data.get("currency") or ctx.get("currency_symbol") or "₹"
                        fmt_cin = res.data.get("formatted_check_in_date") or res.data.get("check_in_date")
                        fmt_cout = res.data.get("formatted_check_out_date") or res.data.get("check_out_date")

                        gw_section = ""
                        if gw:
                            gw_sym = gw.get("currency_symbol") or curr_sym
                            gw_section = (
                                f"\n💳 **Payment Gateway & Checkout**:\n"
                                f"• **Gateway Order ID**: `{gw.get('order_id')}`\n"
                                f"• **Amount Due**: {gw_sym} {gw.get('amount', res.data['total_amount'])}\n"
                                f"• **Payment Link**: [Complete Payment Online]({gw.get('payment_url')})\n"
                            )

                        rt_name = res.data.get("room_type_name")
                        rt_str = f" ({rt_name})" if rt_name else ""
                        rate_val = res.data.get("price_per_night", 0.0)
                        applied_tier = res.data.get("applied_tier")
                        tier_str = f" [{applied_tier['occupancy']} Guest Tier: {curr_sym} {applied_tier['price_per_night']}/night]" if applied_tier else ""
                        reply = (
                            f"🎉 **Reservation Successfully Created!**\n\n"
                            f"• **Booking Reference**: `{res.data['booking_reference']}`\n"
                            f"• **Homestay**: {res.data['property_name']}{rt_str}\n"
                            f"• **Stay Dates**: {fmt_cin} to {fmt_cout}\n"
                            f"• **Guests & Rooms**: {res.data['num_guests']} guest(s), {res.data['num_rooms']} room(s)\n"
                            f"• **Rate**: {curr_sym} {rate_val}/night{tier_str}\n"
                            f"• **Total Amount**: {curr_sym} {res.data['total_amount']}\n"
                            f"• **Guest**: {res.data['guest']['full_name']} ({res.data['guest']['email']})\n"
                            f"{gw_section}\n"
                            f"A confirmation email has been dispatched with check-in instructions. Tashi Delek!"
                        )
                    else:
                        err_text = res.content[0].text if res.content else 'Selected dates or rooms are unavailable.'
                        clean_err = re.sub(r"^Error:\s*", "", err_text)
                        reply = (
                            f"❌ **Booking Creation Blocked**: {clean_err}\n\n"
                            f"Reservation cannot be created because the property or room type is unavailable for your selected dates and room count. "
                            f"Please select different dates or explore other homestays."
                        )
                    intent_name = "checkout_and_book"

        # 4. Availability & Pricing Quote Intent
        elif any(k in msg_lower for k in ["availability", "price", "quote", "cost", "how much", "rate"]):
            if len(date_matches) < 2:
                selected_prop = prop_target
                if selected_prop:
                    details_res = await self.tool_executor.execute_tool("get_homestay_details", {"property_id": selected_prop}, current_user_id)
                    tool_calls.append(AssistantToolCallSchema(tool="get_homestay_details", arguments={"property_id": selected_prop}, result=details_res.data, is_error=details_res.isError))
                    prop_name = (details_res.data or {}).get("name", selected_prop)
                    currency = (details_res.data or {}).get("currency") or ctx.get("default_currency", "INR")
                    curr_sym = (details_res.data or {}).get("currency_symbol") or ctx.get("currency_symbol", "₹")
                    room_types = (details_res.data or {}).get("room_types", [])
                    raw_base_price = (details_res.data or {}).get("base_price", 0.0)
                    base_price = float(raw_base_price) if raw_base_price is not None else 0.0

                    accumulated_data["homestay"] = details_res.data
                    max_g = (details_res.data or {}).get("max_guests") or 2
                    max_r = (details_res.data or {}).get("max_rooms") or 1
                    tot_u = (details_res.data or {}).get("total_units") or max_r
                    cap_v = (details_res.data or {}).get("capacity") or max_g
                    accumulated_data["availability"] = {
                        "property_name": prop_name,
                        "property_slug": (details_res.data or {}).get("slug", selected_prop),
                        "currency": currency,
                        "currency_symbol": curr_sym,
                        "room_types": room_types,
                        "max_guests": max_g,
                        "max_rooms": max_r,
                        "total_units": tot_u,
                        "capacity": cap_v,
                        "is_available": True,
                        "price_per_night": base_price,
                        "subtotal": base_price,
                        "tax_amount": 0.0,
                        "total_amount": base_price,
                        "requires_dates": True,
                    }

                    rt_section = self._format_room_types_summary(room_types, curr_sym, base_price)

                    reply = (
                        f"To check availability and calculate exact pricing for **{prop_name}**, please provide your stay dates and preferred room type:\n\n"
                        f"**Available Room Types & Rates:**\n"
                        f"{rt_section}\n\n"
                        f"Please provide:\n"
                        f"1. 📅 **Check-in & Check-out dates** ({date_fmt})\n"
                        f"2. 👥 **Number of guests & rooms**\n"
                        f"3. 🛏️ **Preferred Room Type**\n"
                    )
                else:
                    dest = None
                    for key, val in cities_map.items():
                        if key in msg_lower:
                            dest = val
                            break
                    stay_ref = f" in {dest.title()}" if dest else ""
                    reply = (
                        f"To check availability and calculate exact pricing{stay_ref}, could you please provide your:\n"
                        f"1. **Check-in date** ({date_fmt})\n"
                        f"2. **Check-out date** ({date_fmt})\n"
                        f"3. **Number of guests / rooms**\n"
                        f"4. **Preferred Room Type**\n\n"
                        f"I'll verify live availability and generate an instant quote for you!"
                    )
                intent_name = "check_stay_availability"
            else:
                target_slug = prop_target
                if not target_slug:
                    dest = None
                    for key, val in cities_map.items():
                        if key in msg_lower:
                            dest = val
                            break
                    if dest:
                        search_res = await self.tool_executor.execute_tool("search_homestays", {"query": dest, "page_size": 1}, current_user_id)
                        props = (search_res.data or {}).get("properties", [])
                        target_slug = props[0]["slug"] if props else None

                if not target_slug:
                    search_res = await self.tool_executor.execute_tool("search_homestays", {"query": "", "page_size": 1}, current_user_id)
                    props = (search_res.data or {}).get("properties", [])
                    target_slug = props[0]["slug"] if props else None

                if not target_slug:
                    target_slug = "homestay"

                res = await self.tool_executor.execute_tool("check_stay_availability", {
                    "property_id": target_slug,
                    "check_in_date": cin,
                    "check_out_date": cout,
                    "num_guests": num_guests,
                    "num_rooms": num_rooms,
                    "room_type_id": room_type_target,
                }, current_user_id)

                tool_calls.append(AssistantToolCallSchema(tool="check_stay_availability", arguments={"property_id": target_slug, "check_in_date": cin, "check_out_date": cout, "room_type_id": room_type_target}, result=res.data, is_error=res.isError))

                if not res.isError and res.data:
                    accumulated_data["availability"] = res.data
                    is_available = res.data.get("is_available", True)
                    nights = res.data.get("nights", res.data.get("num_nights", 1))
                    subtotal = res.data.get("subtotal", res.data.get("base_amount", 0.0))
                    rt_name = res.data.get("selected_room_type")
                    rt_line = f"• **Room Type**: {rt_name}\n" if rt_name else ""
                    curr_sym = res.data.get("currency_symbol") or res.data.get("currency") or ctx.get("currency_symbol") or "₹"
                    fmt_cin = res.data.get("formatted_check_in_date") or res.data.get("check_in_date")
                    fmt_cout = res.data.get("formatted_check_out_date") or res.data.get("check_out_date")

                    if not is_available or res.data.get("available_units", 0) < num_rooms:
                        avail_units = res.data.get("available_units", 0)
                        units_info = f"Only {avail_units} room(s) available for {num_rooms} requested room(s)." if avail_units > 0 else "All rooms are fully booked for these dates."
                        reply = (
                            f"⚠️ **{res.data['property_name']} is currently UNAVAILABLE** for your selected stay dates ({fmt_cin} to {fmt_cout}).\n\n"
                            f"{rt_line}"
                            f"• **Availability Status**: {units_info}\n"
                            f"• **Booking Status**: New bookings cannot be created for these dates.\n\n"
                            f"Would you like to check different dates or explore our other available homestays?"
                        )
                    else:
                        applied_tier = res.data.get("applied_tier")
                        tier_badge = f"• **Active Rate Tier**: ✓ {applied_tier['occupancy']} Guest Tier Active ({curr_sym} {applied_tier['price_per_night']}/night)\n" if applied_tier else ""

                        rts = res.data.get("room_types") or []
                        tiers_breakdown = ""
                        if rts:
                            selected_rt = next((r for r in rts if r.get("name") == rt_name or r.get("is_selected")), rts[0] if len(rts) == 1 else None)
                            if selected_rt and selected_rt.get("pricing_tiers"):
                                tier_strs = [f"{t.get('occupancy')} Guests: {curr_sym} {float(t.get('price_per_night', t.get('base_price', 0.0))):,.0f}" for t in sorted(selected_rt["pricing_tiers"], key=lambda x: x.get('occupancy', 0))]
                                tiers_breakdown = f"• **Room Rates by Occupancy**: {' | '.join(tier_strs)}\n"

                        reply = (
                            f"✨ **Availability Quote for {res.data['property_name']}**\n\n"
                            f"{rt_line}"
                            f"{tier_badge}"
                            f"{tiers_breakdown}"
                            f"• **Dates**: {fmt_cin} to {fmt_cout} ({nights} nights)\n"
                            f"• **Nightly Rate**: {curr_sym} {res.data['price_per_night']}\n"
                            f"• **Subtotal**: {curr_sym} {subtotal}\n"
                            f"• **Taxes & Fees**: {curr_sym} {res.data['tax_amount']}\n"
                            f"• **Total**: **{curr_sym} {res.data['total_amount']}**\n\n"
                            f"Would you like me to book this homestay for you?"
                        )
                else:
                    err_msg = res.content[0].text if res.content else "Selected dates or property unavailable."
                    clean_err = re.sub(r"^Error:\s*", "", err_msg)
                    reply = f"Could not check availability for \"{target_slug}\": {clean_err} Please verify the property name or dates."
                intent_name = "check_stay_availability"

        # 5. Greetings & Help Intent
        elif (
            any(
                re.search(rf"\b{g}\b", msg_lower)
                for g in ["hi", "hello", "hey", "kuzu", "zangpo", "kuzuzangpo", "tashi delek", "good morning", "good evening", "who are you", "help", "what can you do"]
            ) and not any(k in msg_lower for k in ["book", "stay", "homestay", "room", "price", "hotel", "find", "search", "available", "quote", "pay"])
        ):
            cities_str = ", ".join(city_names[:5]) if city_names else "our featured destinations"
            country_str = f" in {country_name}" if country_name else ""
            reply = (
                f"Kuzu Zangpo La! 🙏 Welcome to **{app_name} AI Concierge**.\n\n"
                f"I am your personal travel assistant. Here is how I can help you:\n"
                f"• **Discover Homestays**: Search authentic stays across {cities_str} (by city, neighborhood, or address).\n"
                f"• **Check Availability & Quotes**: Get instant room availability, nightly rates, and tax calculations.\n"
                f"• **Instant Checkout & Online Payment**: Book homestays seamlessly and pay online via secure payment gateway.\n"
                f"• **Track Reservations & Pay**: Check your booking status or complete pending payments.\n\n"
                f"Where{country_str} are you planning to travel?"
            )
            intent_name = "greeting"

        # 6. Popular Destinations Intent
        elif any(k in msg_lower for k in ["destination", "destinations", "places to visit", "popular places", "where to go", "where to stay", "cities"]):
            res = await self.tool_executor.execute_tool("get_popular_destinations", {"limit": 6}, current_user_id)
            tool_calls.append(AssistantToolCallSchema(tool="get_popular_destinations", arguments={"limit": 6}, result=res.data, is_error=res.isError))
            destinations = (res.data or {}).get("destinations", [])
            country_header = f" in {country_name}" if country_name else ""
            reply = f"🏔️ **Top Travel Destinations{country_header}:**\n\n"
            for d in destinations:
                desc = f" — {d['description']}" if d.get('description') else ""
                reply += f"• **{d['name']}**{desc}\n"
            reply += "\nWhich destination would you like to explore homestays for?"
            intent_name = "get_popular_destinations"

        # 7. Search & Discovery Intent (Standard & Semantic Vector Search)
        else:
            dest = None
            for key, val in cities_map.items():
                if key in msg_lower:
                    dest = val
                    break
            
            # Extract page and page_size for pagination
            page_match = re.search(r"\bpage\s*(\d+)\b", msg_lower)
            search_page = int(page_match.group(1)) if page_match else int(guest_details.get("page", 1) or 1)

            size_match = re.search(r"\b(?:limit|size|page_size|count)\s*(\d+)\b", msg_lower)
            search_size = int(size_match.group(1)) if size_match else int(guest_details.get("page_size", 5) or 5)

            # Extract location / neighborhood (e.g. near Motithang, in Motithang)
            loc_match = re.search(r"(?:near|location|area|neighborhood)\s+([\w\s-]+?)(?:\s+at|\s+address|\s+from|\s+in|\s+for|\s+with|\s+page|$)", message, flags=re.IGNORECASE)
            extracted_loc = loc_match.group(1).strip() if loc_match else None
            if extracted_loc and extracted_loc.lower() in cities_map:
                dest = dest or cities_map[extracted_loc.lower()]
                extracted_loc = None

            # Extract street address (e.g. at Norzin Lam, address Norzin Lam, address: Norzin Lam 4)
            addr_match = re.search(r"(?:address[:\s]+|at\s+address[:\s]+|street[:\s]+|road[:\s]+)([\w\s,.-]+?)(?:\s+in|\s+near|\s+from|\s+for|\s+page|$)", message, flags=re.IGNORECASE)
            extracted_addr = addr_match.group(1).strip() if addr_match else None
            if not extracted_addr:
                street_match = re.search(r"\bat\s+([\w\s-]+(?:Lam|Street|Road|Avenue|Lane|Way|Highway|Marg|Drive|Dr|St|Rd|Bldg))\b", message, flags=re.IGNORECASE)
                if street_match:
                    extracted_addr = street_match.group(1).strip()

            # Extract destination/location/property name keyword by stripping common query words
            clean_search = re.sub(r"\b(find|search|show|get|look\s+for|explore|compare|comparison|other|another|different|various|options?|alternatives?|similar|view|browse|list|all|available|homestays?|homstays?|homestay|homstay|propert(?:y|ies)|stays?|rooms?|hotels?|accommodations?|place|places|in|at|near|around|for|please|me|best|top|good|check)\b", "", msg_lower, flags=re.IGNORECASE)
            if extracted_loc:
                clean_search = re.sub(re.escape(extracted_loc.lower()), "", clean_search, flags=re.IGNORECASE)
            if extracted_addr:
                clean_search = re.sub(re.escape(extracted_addr.lower()), "", clean_search, flags=re.IGNORECASE)
            clean_search = re.sub(r"\bpage\s*\d+\b", "", clean_search, flags=re.IGNORECASE)
            clean_search = re.sub(r"\s+", " ", clean_search).strip()

            is_comparison = any(w in msg_lower for w in ["compare", "comparison", "other homestays", "other stays", "more options", "view other", "explore other", "alternative stays", "different homestays"])

            is_semantic = any(w in msg_lower for w in [
                "view", "mountain", "wooden", "cottage", "fire", "bukhari", "peaceful", "quiet",
                "orchard", "meditation", "organic", "farm", "cozy", "traditional", "romantic",
                "bath", "stone", "nature", "vibe", "himalaya", "river", "balcony"
            ])

            if is_semantic:
                res = await self.tool_executor.execute_tool("semantic_search_homestays", {
                    "query": message,
                    "city_name": dest,
                    "limit": search_size,
                }, current_user_id)
                tool_calls.append(AssistantToolCallSchema(tool="semantic_search_homestays", arguments={"query": message, "city_name": dest}, result=res.data, is_error=res.isError))
                props = (res.data or {}).get("properties", [])
                accumulated_data["search_results"] = props
                intent_name = "semantic_search_homestays"

                if props:
                    reply = f"Kuzu Zangpo La! Based on your preference for *'{clean_search or message}'*, here are top matching homestays:\n\n"
                    for i, p in enumerate(props, 1):
                        match_pct = p.get('match_percentage')
                        match_label = f" ({match_pct}% match)" if match_pct else ""
                        loc_part = p.get('location') or p.get('city_name') or p.get('city') or (country_name or 'Homestay')
                        reply += f"**{i}. {p['name']}**{match_label} — {loc_part}\n"
                        price_val = p.get('price_per_night') or p.get('base_price') or 0
                        curr_sym = p.get('currency_symbol') or p.get('currency') or ctx.get('currency_symbol') or '₹'
                        addr_info = f" | Address: {p['address']}" if p.get('address') else ""
                        reply += f"   • Price: {curr_sym} {price_val}/night | Type: {p.get('type') or p.get('property_type') or 'Homestay'}{addr_info}\n\n"
                    reply += "Would you like to view availability dates or book one of these?"
                else:
                    cities_display = ", ".join([f"**{c}**" for c in city_names[:3]]) if city_names else "our featured destinations"
                    reply = (
                        f"I searched our listings for *'{message}'*, but couldn't find an exact atmospheric match. "
                        f"Would you like to explore homestays in {cities_display}?"
                    )
            else:
                search_query = dest or (clean_search if clean_search and clean_search.lower() not in ignored_names else None)
                location_parts = []
                if dest:
                    location_parts.append(dest.capitalize())
                if extracted_loc:
                    location_parts.append(extracted_loc.title())
                if extracted_addr:
                    location_parts.append(extracted_addr.title())
                if not location_parts and clean_search and clean_search.lower() not in ignored_names:
                    location_parts.append(clean_search.title())

                location_label = ", ".join(location_parts) if location_parts else (country_name or "our destinations")

                # Only pass dates to search if user explicitly specified date pattern
                cin_search = date_matches[0] if len(date_matches) >= 1 else None
                cout_search = date_matches[1] if len(date_matches) >= 2 else None
                has_guest_filter = any(w in msg_lower for w in ["guest", "people", "person", "adult"])

                res = await self.tool_executor.execute_tool("search_homestays", {
                    "query": search_query or "",
                    "city_name": dest,
                    "location_name": extracted_loc,
                    "address": extracted_addr,
                    "check_in_date": cin_search,
                    "check_out_date": cout_search,
                    "guests": num_guests if has_guest_filter else None,
                    "rooms": num_rooms if "room" in msg_lower else 1,
                    "page": search_page,
                    "page_size": search_size,
                }, current_user_id)

                tool_calls.append(AssistantToolCallSchema(tool="search_homestays", arguments={
                    "query": search_query or "",
                    "location_name": extracted_loc,
                    "address": extracted_addr,
                    "page": search_page,
                    "page_size": search_size,
                }, result=res.data, is_error=res.isError))

                props = (res.data or {}).get("properties", [])
                total_val = (res.data or {}).get("total", len(props) if isinstance(props, list) else 0)
                if not isinstance(total_val, int):
                    try:
                        total_val = int(total_val)
                    except Exception:
                        total_val = len(props) if isinstance(props, list) else 0
                total_count = total_val

                pages_val = (res.data or {}).get("total_pages")
                if not isinstance(pages_val, int):
                    try:
                        pages_val = int(pages_val)
                    except Exception:
                        pages_val = (total_count + search_size - 1) // search_size if total_count > 0 else 1
                total_pages = max(1, pages_val)

                accumulated_data["search_results"] = props
                accumulated_data["pagination"] = {
                    "page": search_page,
                    "page_size": search_size,
                    "total": total_count,
                    "total_pages": total_pages,
                }

                if props:
                    page_label = f" (Page {search_page} of {total_pages})" if total_pages > 1 else ""
                    if is_comparison:
                        reply = f"Kuzu Zangpo La! Here is a comparison of available homestays in **{location_label}**{page_label}:\n\n"
                    else:
                        reply = f"Kuzu Zangpo La! I found **{total_count} homestay(s)** in {location_label}{page_label}:\n\n"
                    for i, p in enumerate(props, 1):
                        loc_part = p.get('location') or p.get('city') or (country_name or 'Homestay')
                        addr_info = f"\n   • 📍 Address: {p['address']}" if p.get('address') else ""
                        curr_sym = p.get('currency_symbol') or p.get('currency') or ctx.get('currency_symbol') or '₹'
                        rating_val = p.get('rating')
                        reviews_cnt = p.get('review_count', 0)
                        rating_str = f"⭐ {rating_val} ({reviews_cnt} reviews)" if (rating_val is not None and float(rating_val) > 0) or reviews_cnt > 0 else "⭐ New (No reviews yet)"
                        reply += f"**{i}. {p['name']}** ({loc_part})\n"
                        reply += f"   • Price: {curr_sym} {p['base_price']}/night | Rating: {rating_str}{addr_info}\n"
                        reply += f"   • Max Guests: {p['max_guests']} | Type: {p['property_type']}\n\n"
                    
                    if search_page < total_pages:
                        reply += f"👉 *Type 'page {search_page + 1}' to see more homestays.*"
                    elif is_comparison:
                        reply += "Tell me which one you'd like to check dates for, or ask for a detailed price breakdown!"
                    else:
                        reply += "Tell me which one you'd like to check dates for or book!"
                else:
                    cities_display = ", ".join([f"**{c}**" for c in city_names[:3]]) if city_names else "our featured destinations"
                    country_ref = f" in {country_name}" if country_name else ""
                    reply = (
                        f"Kuzu Zangpo La! I searched for homestays in **{location_label}**, but found 0 matching properties in our listings. "
                        f"{app_name} specializes in authentic homestays{country_ref} across destinations like {cities_display}. "
                        f"Would you like to explore those?"
                    )
                intent_name = "search_homestays"


        suggested_actions = self._generate_suggestions(tool_calls, accumulated_data, ctx)

        return AssistantChatDataSchema(
            reply=reply,
            session_id=session_id,
            intent=intent_name if 'intent_name' in locals() else (tool_calls[0].tool if tool_calls else "general_chat"),
            action_taken=f"Executed {tool_calls[0].tool}" if tool_calls else None,
            tool_calls=tool_calls,
            search_results=accumulated_data.get("search_results"),
            availability=accumulated_data.get("availability"),
            booking=accumulated_data.get("booking"),
            user=accumulated_data.get("user"),
            suggested_actions=suggested_actions,
        )


    # --------------------------------------------------------------------------
    # Helper: Suggestion Chips Generator
    # --------------------------------------------------------------------------

    def _generate_suggestions(
        self,
        tool_calls: List[AssistantToolCallSchema],
        data: Dict[str, Any],
        ctx: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        if data.get("payment"):
            if settings.PAYMENT_ENABLED:
                return ["Complete payment now", "View booking status", "Cancellation policy"]
            else:
                return ["View booking status", "Cancellation policy", "Explore nearby attractions"]
        elif data.get("booking"):
            if settings.PAYMENT_ENABLED:
                return ["Complete payment online", "View booking status", "Cancellation policy", "Explore nearby attractions"]
            else:
                return ["View booking status", "Cancellation policy", "Explore nearby attractions"]
        elif data.get("availability"):
            is_avail = data["availability"].get("is_available", True)
            req_dates = data["availability"].get("requires_dates", False)
            if is_avail and not req_dates and settings.PAYMENT_ENABLED:
                return ["Book this homestay now", "Check different dates", "Compare other homestays"]
            else:
                return ["Check different dates", "Compare other homestays", "Explore nearby destinations"]
        elif data.get("search_results"):
            props = data.get("search_results") or []
            first_city = props[0].get("city") if props and props[0].get("city") else None
            c_tag = f" in {first_city}" if first_city else ""
            return [f"Check availability for top homestay", f"Filter by price under 3000", f"Explore homestays{c_tag}"]
        
        city_names = ctx.get("city_names", []) if ctx else []
        country_name = ctx.get("country_name", "") if ctx else ""
        c1 = city_names[0] if len(city_names) > 0 else "top destinations"
        c2 = city_names[1] if len(city_names) > 1 else c1
        country_suffix = f" in {country_name}" if country_name else ""
        return [
            f"Find homestays in {c1}",
            f"Homestays in {c2}",
            "Check my booking status",
            f"Popular destinations{country_suffix}",
        ]

