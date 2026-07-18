from typing import Optional, TypedDict

from sqlalchemy import select

from app.models.login_log_model import LoginLog
from app.repositories.base_repository import BaseRepository, Page


class WithRelations(TypedDict, total=False):
    # e.g. "orders": bool, "profile": bool
    user : bool


class LoginLogRepository(BaseRepository[LoginLog]):

    _relation_map = {
        "user": LoginLog.user,
    }
    async def create(
        self,
        login_log: LoginLog,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True
    ) -> LoginLog:
        self.db.add(login_log)

        if not commit:
            return login_log
        
        if with_relations:
            query = self._apply_relations(
                select(LoginLog).where(LoginLog.id == login_log.id),
                with_relations,
                self._relation_map,
            )
            # Data was just committed, so no flush is needed here.
            await self.db.commit()
            return await self._fetch_one(query)
        return login_log

    
    async def list_by_user_id(
        self,
        user_id: int,
        with_relations: Optional[WithRelations] = None,
        page: Optional[int] = None,
        page_size: Optional[int] = None,
        flush: bool = False
    ) -> Page[LoginLog]:
        query = self._apply_relations(
            select(LoginLog).where(LoginLog.user_id == user_id),
            with_relations,
            self._relation_map,
        )
        if page is not None and page_size is not None:
            offset = (page - 1) * page_size
            query = query.offset(offset).limit(page_size)
        
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
    