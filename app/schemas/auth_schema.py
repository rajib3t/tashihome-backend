

from typing import Optional

from pydantic import BaseModel

from app.schemas.response import BaseResponse
from app.schemas.token_schema import AccessTokenSchema, TokenDataSchema
from app.schemas.user_schema import UserData


class LoginResponseData(BaseModel):
    user: UserData
    token: AccessTokenSchema

class LoginResponse(BaseResponse):
    data: LoginResponseData


class LoginData(BaseModel):
    user: UserData
    token: TokenDataSchema

class RefreshTokenResponse(BaseResponse):
    data: AccessTokenSchema

class RegisterUserResponseData(BaseModel):
    full_name: str
    email: str
    phone: Optional[str] = None

class RegisterResponse(BaseResponse):
    data: RegisterUserResponseData


class ActiveAccountUserData(BaseModel):
    id: str
    name: Optional[str] = None
    full_name: Optional[str] = None
    email: str
    status: str
    role: Optional[str] = None


class ActiveAccountResponseData(BaseModel):
    status: str
    user: ActiveAccountUserData


class ActiveAccountResponse(BaseResponse):
    data: ActiveAccountResponseData

