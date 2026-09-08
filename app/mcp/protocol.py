from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field


# ------------------------------------------------------------------------------
# JSON-RPC 2.0 Base Protocol
# ------------------------------------------------------------------------------

class JSONRPCError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None


class JSONRPCRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: str
    params: Optional[Dict[str, Any]] = None


class JSONRPCResponse(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None


# ------------------------------------------------------------------------------
# MCP Tool Protocol Schemas
# ------------------------------------------------------------------------------

class Tool(BaseModel):
    name: str
    description: str
    inputSchema: Dict[str, Any] = Field(default_factory=dict)


class ToolListResult(BaseModel):
    tools: List[Tool]


class CallToolParams(BaseModel):
    name: str
    arguments: Optional[Dict[str, Any]] = Field(default_factory=dict)


class CallToolRequest(BaseModel):
    jsonrpc: Literal["2.0"] = "2.0"
    id: Optional[Union[str, int]] = None
    method: Literal["tools/call"] = "tools/call"
    params: CallToolParams


class TextContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class CallToolResult(BaseModel):
    content: List[TextContent] = Field(default_factory=list)
    isError: bool = False
    data: Optional[Any] = None


# ------------------------------------------------------------------------------
# MCP Resource Protocol Schemas
# ------------------------------------------------------------------------------

class Resource(BaseModel):
    uri: str
    name: str
    description: Optional[str] = None
    mimeType: Optional[str] = "application/json"


class ResourceListResult(BaseModel):
    resources: List[Resource]


class ResourceContent(BaseModel):
    uri: str
    mimeType: Optional[str] = "application/json"
    text: Optional[str] = None
    blob: Optional[str] = None


class ReadResourceResult(BaseModel):
    contents: List[ResourceContent]


# ------------------------------------------------------------------------------
# MCP Prompt Protocol Schemas
# ------------------------------------------------------------------------------

class PromptArgument(BaseModel):
    name: str
    description: Optional[str] = None
    required: bool = False


class Prompt(BaseModel):
    name: str
    description: Optional[str] = None
    arguments: Optional[List[PromptArgument]] = Field(default_factory=list)


class PromptListResult(BaseModel):
    prompts: List[Prompt]


class PromptMessageContent(BaseModel):
    type: Literal["text"] = "text"
    text: str


class PromptMessage(BaseModel):
    role: Literal["user", "assistant", "system"] = "user"
    content: PromptMessageContent


class GetPromptResult(BaseModel):
    description: Optional[str] = None
    messages: List[PromptMessage] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# MCP Initialize Protocol Schemas
# ------------------------------------------------------------------------------

class ServerCapabilities(BaseModel):
    tools: Optional[Dict[str, Any]] = Field(default_factory=dict)
    resources: Optional[Dict[str, Any]] = Field(default_factory=dict)
    prompts: Optional[Dict[str, Any]] = Field(default_factory=dict)


class ServerInfo(BaseModel):
    name: str
    version: str


class InitializeResult(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: ServerCapabilities
    serverInfo: ServerInfo

