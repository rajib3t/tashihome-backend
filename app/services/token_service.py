from typing import Optional

from app.models.token_model import Token
from app.repositories.login_log_repository import WithRelations
from app.repositories.token_repository import TokenRepository


class TokenService:
    
    def __init__(
            self,
            token_repository : TokenRepository,
        ):  
        self.token_repository = token_repository
    async def create(
            self,
            token: Token,
            with_relations: Optional[WithRelations] = None,
            commit: bool = True
    ):
        # This method creates a new token in the database, optionally including related data and controlling whether to commit the transaction.
        return await self.token_repository.create(
            token,
            with_relations=with_relations,
            commit=commit
        )
    
    async def get_by_token(
            self,
            token_str: str,
            with_relations: Optional[WithRelations] = None,
            flush: bool = False
    ):
        # This method retrieves a token from the database by its string representation, optionally controlling whether to flush the session.
        return await self.token_repository.get_by_token(
            token_str,
            with_relations=with_relations,
            flush=flush
        )

    async def get_active_tokens_by_user_id_and_type(
            self,
            user_id: int,
            token_type: str,
           
            flush: bool = False
    ):
        # This method retrieves a token from the database by the associated user ID, optionally controlling whether to flush the session.
        return await self.token_repository.get_active_tokens_by_user_id_and_type(
            user_id,
            token_type,
            flush=flush
        )

    async def revoke_token(
            self,
            token: Token,
            commit: bool = True
    ):
        return await self.token_repository.revoke_token(token, commit=commit)

    async def delete_token(
            self,
            token: Token,
            commit: bool = True
    ):
        return await self.token_repository.delete_token(token, commit=commit)
