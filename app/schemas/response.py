from pydantic import BaseModel

class BaseResponse(BaseModel):
    status: str
    message: str


class PaginationMeta(BaseModel):
    total: int
    page: int
    size: int

class PaginationResponse(BaseResponse):
    meta: PaginationMeta
    