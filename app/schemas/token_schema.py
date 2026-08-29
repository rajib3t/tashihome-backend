from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict

from app.models.token_model import TokenType


class TokenSchema(BaseModel):
    token: str
    type: str
    user_id: int
    expires_at: datetime | str
    is_revoked: bool

    model_config = ConfigDict(from_attributes=True)


class AccessTokenSchema(BaseModel):
    type: str = TokenType.ACCESS.value
    token: str

class TokenDataSchema(BaseModel):
    access_token: AccessTokenSchema
    refresh_token: str
