from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.response import BaseResponse


class AssistantToolCallSchema(BaseModel):
    tool: str
    arguments: Optional[Dict[str, Any]] = None
    result: Optional[Any] = None
    is_error: bool = False


class AssistantChatDataSchema(BaseModel):
    reply: str = Field(..., description="Assistant's natural language reply.")
    session_id: Optional[str] = Field(default=None, description="Conversation session ID.")
    intent: Optional[str] = Field(default=None, description="Detected intent / action category.")
    action_taken: Optional[str] = Field(default=None, description="Summary of action performed.")
    tool_calls: List[AssistantToolCallSchema] = Field(default_factory=list, description="List of MCP tools executed.")
    search_results: Optional[List[Dict[str, Any]]] = Field(default=None, description="Homestays list if search performed.")
    pagination: Optional[Dict[str, Any]] = Field(default=None, description="Pagination metadata for search results (page, page_size, total, total_pages, has_next, has_prev).")
    availability: Optional[Dict[str, Any]] = Field(default=None, description="Availability quote details if checked.")
    booking: Optional[Dict[str, Any]] = Field(default=None, description="Booking confirmation details if checkout completed.")
    user: Optional[Dict[str, Any]] = Field(default=None, description="Guest / user info if registered.")
    suggested_actions: Optional[List[str]] = Field(default_factory=list, description="Suggested next action chips for frontend UI.")


class AssistantChatResponseSchema(BaseResponse):
    data: Optional[AssistantChatDataSchema] = None


class AssistantSuggestionItemSchema(BaseModel):
    title: str
    prompt: str
    category: str  # e.g., "search", "booking", "explore"


class AssistantSuggestionsDataSchema(BaseModel):
    suggestions: List[AssistantSuggestionItemSchema] = Field(default_factory=list)


class AssistantSuggestionsResponseSchema(BaseResponse):
    data: Optional[AssistantSuggestionsDataSchema] = None


class SemanticSearchResultItemSchema(BaseModel):
    id: str = Field(..., description="Public UUID of the homestay.")
    name: str
    slug: str
    city_name: Optional[str] = None
    price_per_night: float
    type: Optional[str] = None
    similarity_score: float
    match_percentage: float


class SemanticSearchDataSchema(BaseModel):
    query: str
    total_matches: int
    results: List[SemanticSearchResultItemSchema] = Field(default_factory=list)


class SemanticSearchResponseSchema(BaseResponse):
    data: Optional[SemanticSearchDataSchema] = None


class VectorSyncDataSchema(BaseModel):
    indexed_count: int
    total_indexed: int
    last_synced_at: Optional[str] = None
    s3_persisted: bool = False
    s3_bucket: Optional[str] = None
    s3_key: Optional[str] = None


class VectorSyncResponseSchema(BaseResponse):
    data: Optional[VectorSyncDataSchema] = None


class VectorS3PersistDataSchema(BaseModel):
    success: bool
    persisted: bool
    bucket: str
    key: str
    total_saved: int
    last_synced_at: Optional[str] = None


class VectorS3PersistResponseSchema(BaseResponse):
    data: Optional[VectorS3PersistDataSchema] = None


class VectorS3LoadDataSchema(BaseModel):
    success: bool
    loaded_count: int
    total_indexed: int
    bucket: str
    key: str
    last_synced_at: Optional[str] = None


class VectorS3LoadResponseSchema(BaseResponse):
    data: Optional[VectorS3LoadDataSchema] = None



