from typing import TypedDict, Optional

from sqlalchemy import select

from app.models.user_model import User
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    # e.g. "orders": bool, "profile": bool
    pass


class UserRepository(BaseRepository[User]):

    _relation_map = {
        # e.g. "orders": User.orders, "profile": User.profile
    }

    async def create(
        self,
        user: User,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> User:
        self.db.add(user)

        if not commit:
            return user

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(User).where(User.id == user.id),
                with_relations,
                self._relation_map,
            )
            # Data was just committed, so no flush is needed here.
            await self.db.commit()
            return await self._fetch_one(query)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(
        self,
        user_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[User]:
        query = self._apply_relations(
            select(User).where(User.id == user_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[User]:
        query = self._apply_relations(
            select(User).where(User.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)
    
    async def get_by_email(
        self,
        email: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[User]:
        query = self._apply_relations(
            select(User).where(User.email == email),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def list_users(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[User]:
        query = select(User).order_by(User.created_at.desc())
        query = self._apply_search(query, search, search_fields=[User.full_name])
        query = self._apply_relations(query, with_relations, self._relation_map)

        return await self._paginate(query, page=page, page_size=page_size, flush=flush)