#!/usr/bin/env python3
"""Standalone stdio MCP server runner for TashiHome.

Allows external MCP clients (Claude Desktop, Cursor, Antigravity, etc.)
to connect to TashiHome tools, resources, and prompts over standard input/output.
"""

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.database import async_session_factory
from app.events.event_bus import event_bus
from app.mcp.prompts import MCPPromptHandler
from app.mcp.resources import MCPResourceHandler
from app.mcp.server import TashiHomeMCPServer
from app.mcp.tools import MCPToolExecutor
from app.repositories.booking_repository import BookingRepository
from app.repositories.city_repository import CityRepository
from app.repositories.location_repository import LocationRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.repositories.review_repository import ReviewRepository
from app.repositories.room_block_repository import RoomBlockRepository
from app.repositories.room_type_repository import RoomTypeRepository
from app.repositories.setting_repository import SettingRepository
from app.repositories.tax_repository import TaxRepository
from app.repositories.user_repository import UserRepository
from app.services.booking_service import BookingService
from app.services.city_service import CityService
from app.services.location_service import LocationService
from app.services.property_room_type_service import PropertyRoomTypeService
from app.services.property_service import PropertyService
from app.services.review_service import ReviewService
from app.services.room_type_service import RoomTypeService
from app.services.setting_service import SettingService
from app.services.tax_service import TaxService
from app.services.user_service import UserService


async def run_stdio_server():
    async with async_session_factory() as session:
        prop_repo = PropertyRepository(session)
        booking_repo = BookingRepository(session)
        user_repo = UserRepository(session)
        city_repo = CityRepository(session)
        loc_repo = LocationRepository(session)
        rt_repo = RoomTypeRepository(session)
        prt_repo = PropertyRoomTypeRepository(session)
        tax_repo = TaxRepository(session)
        set_repo = SettingRepository(session)
        rev_repo = ReviewRepository(session)
        block_repo = RoomBlockRepository(session)

        prop_service = PropertyService(prop_repo)
        booking_service = BookingService(
            booking_repository=booking_repo,
            room_block_repository=block_repo,
            property_room_type_repository=prt_repo,
        )
        user_service = UserService(user_repo)
        city_service = CityService(city_repo)
        loc_service = LocationService(loc_repo)
        rt_service = RoomTypeService(rt_repo)
        prt_service = PropertyRoomTypeService(prt_repo)
        tax_service = TaxService(tax_repo)
        set_service = SettingService(set_repo)
        rev_service = ReviewService(rev_repo)

        tool_executor = MCPToolExecutor(
            property_service=prop_service,
            booking_service=booking_service,
            user_service=user_service,
            city_service=city_service,
            location_service=loc_service,
            room_type_service=rt_service,
            property_room_type_service=prt_service,
            tax_service=tax_service,
            setting_service=set_service,
            review_service=rev_service,
            event_bus=event_bus,
        )

        server = TashiHomeMCPServer(
            tool_executor=tool_executor,
            resource_handler=MCPResourceHandler(city_service, prop_service),
            prompt_handler=MCPPromptHandler(),
        )

        loop = asyncio.get_running_loop()
        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await loop.connect_read_pipe(lambda: protocol, sys.stdin)

        while True:
            line_bytes = await reader.readline()
            if not line_bytes:
                break
            line = line_bytes.decode("utf-8").strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
                response = await server.handle_jsonrpc(payload)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as e:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Fatal parse error: {str(e)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


if __name__ == "__main__":
    try:
        asyncio.run(run_stdio_server())
    except (KeyboardInterrupt, SystemExit):
        pass

