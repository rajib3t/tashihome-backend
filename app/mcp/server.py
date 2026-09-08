import logging
from typing import Any, Dict, Optional

from app.core.config import settings
from app.mcp.protocol import (
    InitializeResult,
    JSONRPCError,
    JSONRPCRequest,
    JSONRPCResponse,
    PromptListResult,
    ReadResourceResult,
    ResourceListResult,
    ServerCapabilities,
    ServerInfo,
    ToolListResult,
)
from app.mcp.prompts import ALL_PROMPTS, MCPPromptHandler
from app.mcp.resources import MCPResourceHandler
from app.mcp.tools import ALL_MCP_TOOLS, MCPToolExecutor

logger = logging.getLogger(__name__)


class TashiHomeMCPServer:
    """Standard Model Context Protocol (MCP) Server for TashiHome.

    Processes JSON-RPC 2.0 requests for tool invocations, resources, and prompt templates.
    """

    def __init__(
        self,
        tool_executor: MCPToolExecutor,
        resource_handler: Optional[MCPResourceHandler] = None,
        prompt_handler: Optional[MCPPromptHandler] = None,
        server_name: Optional[str] = None,
        server_version: Optional[str] = None,
    ):
        self.tool_executor = tool_executor
        self.resource_handler = resource_handler or MCPResourceHandler()
        self.prompt_handler = prompt_handler or MCPPromptHandler()
        self.server_name = server_name or getattr(settings, "MCP_SERVER_NAME", "tashihome-mcp-server")
        self.server_version = server_version or getattr(settings, "MCP_SERVER_VERSION", "1.0.0")

    async def handle_jsonrpc(
        self,
        payload: Dict[str, Any],
        current_user_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Handle a single incoming JSON-RPC 2.0 request dictionary and return JSON-RPC response."""
        try:
            req = JSONRPCRequest(**payload)
        except Exception as e:
            return JSONRPCResponse(
                id=payload.get("id"),
                error=JSONRPCError(code=-32700, message=f"Parse error / Invalid JSON-RPC request: {str(e)}"),
            ).model_dump()

        res = await self.process_request(req, current_user_id=current_user_id)
        return res.model_dump(exclude_none=True)

    async def process_request(
        self,
        request: JSONRPCRequest,
        current_user_id: Optional[int] = None,
    ) -> JSONRPCResponse:
        """Process validated JSONRPCRequest."""
        method = request.method
        params = request.params or {}

        try:
            if method == "initialize":
                result = InitializeResult(
                    protocolVersion="2024-11-05",
                    capabilities=ServerCapabilities(
                        tools={"listChanged": False},
                        resources={"subscribe": False, "listChanged": False},
                        prompts={"listChanged": False},
                    ),
                    serverInfo=ServerInfo(name=self.server_name, version=self.server_version),
                )
                return JSONRPCResponse(id=request.id, result=result.model_dump())

            elif method == "ping":
                return JSONRPCResponse(id=request.id, result={})

            elif method == "tools/list":
                result = ToolListResult(tools=ALL_MCP_TOOLS)
                return JSONRPCResponse(id=request.id, result=result.model_dump())

            elif method == "tools/call":
                tool_name = params.get("name")
                tool_args = params.get("arguments") or {}
                if not tool_name:
                    return JSONRPCResponse(
                        id=request.id,
                        error=JSONRPCError(code=-32602, message="Missing 'name' in tool call parameters."),
                    )

                call_result = await self.tool_executor.execute_tool(
                    tool_name=tool_name,
                    arguments=tool_args,
                    current_user_id=current_user_id,
                )
                return JSONRPCResponse(id=request.id, result=call_result.model_dump())

            elif method == "resources/list":
                resources = await self.resource_handler.list_resources()
                return JSONRPCResponse(id=request.id, result=ResourceListResult(resources=resources).model_dump())

            elif method == "resources/read":
                uri = params.get("uri")
                if not uri:
                    return JSONRPCResponse(
                        id=request.id,
                        error=JSONRPCError(code=-32602, message="Missing 'uri' in resource read parameters."),
                    )
                read_res = await self.resource_handler.read_resource(uri)
                return JSONRPCResponse(id=request.id, result=read_res.model_dump())

            elif method == "prompts/list":
                prompts = await self.prompt_handler.list_prompts()
                return JSONRPCResponse(id=request.id, result=PromptListResult(prompts=prompts).model_dump())

            elif method == "prompts/get":
                name = params.get("name")
                args = params.get("arguments") or {}
                if not name:
                    return JSONRPCResponse(
                        id=request.id,
                        error=JSONRPCError(code=-32602, message="Missing 'name' in prompt get parameters."),
                    )
                prompt_res = await self.prompt_handler.get_prompt(name, args)
                return JSONRPCResponse(id=request.id, result=prompt_res.model_dump())

            else:
                return JSONRPCResponse(
                    id=request.id,
                    error=JSONRPCError(code=-32601, message=f"Method not found: '{method}'"),
                )

        except Exception as e:
            logger.exception("Error processing MCP request for method %s: %s", method, e)
            return JSONRPCResponse(
                id=request.id,
                error=JSONRPCError(code=-32603, message=f"Internal server error: {str(e)}"),
            )

