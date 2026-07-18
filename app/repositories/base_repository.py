from dataclasses import dataclass
from typing import Optional, Any, Generic, TypeVar, Sequence

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import Select
from sqlalchemy.sql.elements import ColumnElement

ModelT = TypeVar("ModelT")


@dataclass
class Page(Generic[ModelT]):
    """Result of a paginated query."""

    items: list[ModelT]
    total: int
    page: int
    page_size: int

    @property
    def pages(self) -> int:
        if self.page_size <= 0:
            return 0
        return (self.total + self.page_size - 1) // self.page_size


class BaseRepository(Generic[ModelT]):
    """
    Base repository providing shared query helpers for async SQLAlchemy sessions.

    Conventions used across subclasses:
      - Write methods (create/update/delete) own `commit()` — they end the
        transaction and persist changes.
      - Read methods (get_*) never commit. If they need to see uncommitted
        pending changes in the current session, they `flush()` instead,
        which pushes SQL to the DB without ending the transaction.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    def _apply_relations(
        self,
        query: Select,
        with_relations: Optional[dict[str, bool]] = None,
        relation_map: Optional[dict[str, Any]] = None,
    ) -> Select:
        if not with_relations or not relation_map:
            return query

        for relation, enabled in with_relations.items():
            if enabled and relation in relation_map:
                query = query.options(selectinload(relation_map[relation]))

        return query

    def _apply_search(
        self,
        query: Select,
        search: Optional[str],
        search_fields: Optional[Sequence[ColumnElement]] = None,
    ) -> Select:
        """
        Apply a case-insensitive substring search across one or more columns.

        `search_fields` are the model columns to match against (e.g.
        [User.name, User.email]). Terms match if any field contains
        `search` (OR'd together). Empty/whitespace-only search terms and
        an empty `search_fields` list are both treated as "no filter".
        """
        if not search or not search_fields:
            return query

        term = f"%{search.strip()}%"
        conditions = [field.ilike(term) for field in search_fields]

        return query.where(or_(*conditions))

    async def _fetch_one(self, query: Select, flush: bool = False) -> Optional[ModelT]:
        """
        Execute a query and return a single result (or None).

        `flush` should only be set True when the caller needs pending,
        uncommitted changes in this session reflected in the query results.
        It never ends the transaction, unlike commit().
        """
        if flush:
            await self.db.flush()

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def _fetch_all(self, query: Select, flush: bool = False) -> list[ModelT]:
        if flush:
            await self.db.flush()

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def _paginate(
        self,
        query: Select,
        page: int = 1,
        page_size: int = 20,
        flush: bool = False,
    ) -> Page[ModelT]:
        """
        Paginate a SELECT query.

        Runs a COUNT(*) over the query's current filters/joins (via a
        subquery, so ordering/columns on `query` don't interfere), then
        applies LIMIT/OFFSET to fetch just the requested page of rows.

        `page` is 1-indexed. Invalid values are clamped (page >= 1,
        page_size >= 1).
        """
        page = max(page, 1)
        page_size = max(page_size, 1)

        if flush:
            await self.db.flush()

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar_one()

        paged_query = query.limit(page_size).offset((page - 1) * page_size)
        result = await self.db.execute(paged_query)
        items = list(result.scalars().all())

        return Page(items=items, total=total, page=page, page_size=page_size)