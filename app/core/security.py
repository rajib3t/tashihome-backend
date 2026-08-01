from pwdlib import PasswordHash
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta, timezone
from uuid import UUID

import asyncio

from pydantic import BaseModel


from app.core.config import settings
from app.core.exceptions import TokenExpiredError, TokenInvalidError
from app.models.token_model import TokenType
class PasswordHasher:
    def __init__(self):
        self.hasher = PasswordHash.recommended()

    async def hash_password(self, password: str) -> str:
        return await asyncio.get_event_loop().run_in_executor(None, self.hasher.hash, password)

    async def verify_password(self, password: str, hashed_password: str) -> bool:
        return await asyncio.get_event_loop().run_in_executor(None, self.hasher.verify, password, hashed_password)

    
class Token(BaseModel):
    user_id: int
    type: str
    token: str
    is_revoked: bool
    expires_at: datetime


class TokenManager:
    @staticmethod
    def _encode_jwt(payload: dict) -> str:
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def _decode_jwt(token: str) -> dict:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])

    @staticmethod
    async def _normalize_claim_value(value):
        if isinstance(value, UUID):
            return str(value)
        if isinstance(value, dict):
            return {k: await TokenManager._normalize_claim_value(v) for k, v in value.items()}
        if isinstance(value, list):
            return [await TokenManager._normalize_claim_value(item) for item in value]
        if isinstance(value, tuple):
            return tuple(await TokenManager._normalize_claim_value(item) for item in value)
        return value

    @classmethod
    async def _normalize_claims(cls, claims: dict | None) -> dict:
        if not claims:
            return {}
        return {key: await cls._normalize_claim_value(value) for key, value in claims.items()}

    async def create_access_token(self, data: dict, additional_claims: dict = None) -> str:
        to_encode = await self._normalize_claims(data)
        if additional_claims:
            to_encode.update(await self._normalize_claims(additional_claims))

        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode.update({"iat": now, "exp": expire, "type": TokenType.ACCESS})
        return await asyncio.get_event_loop().run_in_executor(None, self._encode_jwt, to_encode)

    async def create_refresh_token(self, data: dict, additional_claims: dict = None) -> str:
        to_encode = await self._normalize_claims(data)
        if additional_claims:
            to_encode.update(await self._normalize_claims(additional_claims))

        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        to_encode.update({"iat": now, "exp": expire, "type": TokenType.REFRESH})
        return await asyncio.get_event_loop().run_in_executor(None, self._encode_jwt, to_encode)

    async def email_verify_token(self, public_id: str) -> str:
        to_encode = await self._normalize_claims({"sub": public_id})
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            hours=settings.EMAIL_VERIFY_TOKEN_EXPIRE_HOURS
        )
        to_encode.update({"iat": now, "exp": expire, "type": TokenType.EMAIL_VERIFICATION})
        return await asyncio.get_event_loop().run_in_executor(None, self._encode_jwt, to_encode)

    async def account_activation_token(self, public_id : str) ->str:
        to_encode = await self._normalize_claims({"sub" : public_id})
        now = datetime.now(timezone.utc)
        expire = now + timedelta(
            hours=settings.ACCOUNT_ACTIVATION_HOURS
        )
        to_encode.update({"iat": now, "exp": expire, "type": TokenType.ACCOUNT_ACTIVATION})
        return await asyncio.get_event_loop().run_in_executor(None, self._encode_jwt, to_encode)

    async def generate_reset_token(self, public_id: int, expires_at: datetime) -> str:
        to_encode = await self._normalize_claims({"sub": public_id})
        expire = expires_at
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "type": TokenType.PASSWORD_RESET})
        return await asyncio.get_event_loop().run_in_executor(None, self._encode_jwt, to_encode)

    async def decode_token(self, token: str) -> dict:
        try:
            return await asyncio.get_event_loop().run_in_executor(None, self._decode_jwt, token)
        except ExpiredSignatureError as e:
            raise TokenExpiredError() from e
        except InvalidTokenError as e:
            raise TokenInvalidError("Invalid token") from e
        
    
