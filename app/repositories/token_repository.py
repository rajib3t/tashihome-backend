from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.token_model import Token

from app.repositories.base_repository import BaseRepository

class WithRelations(TypedDict, total=False):
    # e.g. "user": bool
    user: bool

class TokenRepository(BaseRepository[Token]):
    
    _relation_map = {
        "user": Token.user,
    }
    async def create(
        self,
        token: Token,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True
    ) -> Token:
        
        self.db.add(token)

        if not commit:
            return token
        await self.db.commit()
        if with_relations:
            query = self._apply_relations(
                select(Token).where(Token.id == token.id),
                with_relations,
                self._relation_map,
            )
            # Data was just committed, so no flush is needed here.
            await self.db.commit()
            return await self._fetch_one(query)
        await self.db.commit()
        await self.db.refresh(token)
        return token
    

    async def get_by_token(
        self,
        token_str: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False
    ) -> Optional[Token]:
        query = select(Token).where(Token.token == token_str)
        if with_relations:
            query = self._apply_relations(
                query,
                with_relations,
                self._relation_map,
            )
        return await self._fetch_one(query, flush=flush)
    
    async def revoke_token(
        self,
        token: Token,
        commit: bool = True
    ) -> Token:
        token.is_revoked = True
        self.db.add(token)

        if not commit:
            return token

        await self.db.commit()
        await self.db.refresh(token)
        return token
    
    async def delete_token(
        self,
        token: Token,
        commit: bool = True
    ) -> None:
        await self.db.delete(token)

        if not commit:
            return

        await self.db.commit()

    
    async def get_active_tokens_by_user_id(
        self,
        user_id: int,
        flush: bool = False
    ) -> list[Token]:
        query = select(Token).where(Token.user_id == user_id, Token.is_revoked == False)
        return await self._fetch_all(query, flush=flush)
    
    async def revoke_tokens_by_user_id(
        self,
        user_id: int,
        commit: bool = True
    ) -> None:
        query = select(Token).where(Token.user_id == user_id, Token.is_revoked == False)
        tokens = await self._fetch_all(query)

        for token in tokens:
            token.is_revoked = True
            self.db.add(token)

        if not commit:
            return

        await self.db.commit()

    
