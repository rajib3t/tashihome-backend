import asyncio
import json
import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.base_controller import BaseController
from app.deps.assistant import get_mcp_server
from app.deps.auth import CurrentUser, get_optional_current_user
from app.mcp.server import TashiHomeMCPServer
from app.utils.exception_decorate import handle_api_exceptions

logger = logging.getLogger(__name__)


class PublicMCPController(BaseController):
    def __init__(self):
        self.router = APIRouter(
            prefix="/mcp",
            tags=["Public - Model Context Protocol (MCP)"],
        )
        self._register_routes()

    def _register_routes(self):
        routes = [
            ("post", "/rpc", self._handle_rpc, {"response_model": dict}),
            ("get", "/tools", self._list_tools, {"response_model": dict}),
            ("get", "/resources", self._list_resources, {"response_model": dict}),
            ("get", "/prompts", self._list_prompts, {"response_model": dict}),
            ("get", "/sse", self._handle_sse, {}),
            ("post", "/messages", self._handle_messages, {"response_model": dict}),
        ]
        for method, path, handler, route_kwargs in routes:
            self.router.add_api_route(path, handler, methods=[method.upper()], **route_kwargs)

    @handle_api_exceptions
    async def _handle_rpc(
        self,
        payload: Dict[str, Any] = Body(...),
        current_user: Optional[CurrentUser] = Depends(get_optional_current_user),
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        user_id = current_user.id if current_user else None
        response = await mcp_server.handle_jsonrpc(payload, current_user_id=user_id)
        return response

    @handle_api_exceptions
    async def _list_tools(
        self,
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        req = {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
        res = await mcp_server.handle_jsonrpc(req)
        return self.build_response(message="MCP tools retrieved successfully.", data=res.get("result"))

    @handle_api_exceptions
    async def _list_resources(
        self,
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        req = {"jsonrpc": "2.0", "id": 1, "method": "resources/list", "params": {}}
        res = await mcp_server.handle_jsonrpc(req)
        return self.build_response(message="MCP resources retrieved successfully.", data=res.get("result"))

    @handle_api_exceptions
    async def _list_prompts(
        self,
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        req = {"jsonrpc": "2.0", "id": 1, "method": "prompts/list", "params": {}}
        res = await mcp_server.handle_jsonrpc(req)
        return self.build_response(message="MCP prompts retrieved successfully.", data=res.get("result"))

    async def _handle_sse(
        self,
        request: Request,
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        """Server-Sent Events endpoint for MCP client connections."""
        async def event_generator():
            endpoint_msg = {"type": "endpoint", "url": "/api/v1/public/mcp/messages"}
            yield f"event: endpoint\ndata: {json.dumps(endpoint_msg)}\n\n"
            while True:
                if await request.is_disconnected():
                    break
                await asyncio.sleep(15)
                yield f": keepalive\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @handle_api_exceptions
    async def _handle_messages(
        self,
        payload: Dict[str, Any] = Body(...),
        current_user: Optional[CurrentUser] = Depends(get_optional_current_user),
        mcp_server: TashiHomeMCPServer = Depends(get_mcp_server),
    ):
        user_id = current_user.id if current_user else None
        response = await mcp_server.handle_jsonrpc(payload, current_user_id=user_id)
        return response


controller = PublicMCPController()
router = controller.router

