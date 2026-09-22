from typing import Optional
from pydantic import BaseModel

class BaseResponse(BaseModel):
    status: str
    message: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int
    total_pages: Optional[int] = None

class PaginationResponse(BaseResponse):
    meta: Optional[PaginationMeta] = None
    