from pydantic import BaseModel

from app.models.token_model import TokenType


class TokenSchema(BaseModel):
    token: str
    type: str
    user_id: int
    expires_at: str
    is_revoked: bool

    class Config:
        orm_mode = True


class AccessTokenSchema(BaseModel):
    type: str = TokenType.ACCESS
    token: str

class TokenDataSchema(BaseModel):
    access_token: AccessTokenSchema
    refresh_token: str