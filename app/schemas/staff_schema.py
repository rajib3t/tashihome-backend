from app.schemas.response import BaseResponse, PaginationResponse
from app.schemas.user_schema import UserData


class StaffResponseSchema(BaseResponse):
    data: UserData


class StaffListResponseSchema(PaginationResponse):
    data: list[UserData]

