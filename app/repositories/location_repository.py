from __future__ import annotations
from typing import Optional, TypedDict

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.city_model import City
from app.models.location_model import Location
from app.repositories.base_repository import BaseRepository, Page

class WithRelations(TypedDict, total=False):
    city: bool

class LocationRepository(BaseRepository[Location]):
    _relation_map = {
        "city": Location.city
    }
    _filter_map = {
        "name": Location.name,
        "slug": Location.slug,
        "status": Location.status,
        "city_id": Location.city_id,
        "public_id": Location.public_id,
    }

    def _with_city_country(self, query):
        return query.options(
            selectinload(Location.city).selectinload(City.country)
        )


    async def create(
        self,
        location: Location,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Location:
            
        self.db.add(location)
        if commit:
            await self.db.commit()
            await self.db.refresh(location)
        return location

    async def get_by_name_and_city_id(
        self,
        name: str,
        city_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        query = self._apply_relations(
            select(Location).where(
                Location.city_id == city_id,
                Location.name.ilike(name.strip()),
            ),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_slug_and_city_id(
        self,
        slug: str,
        city_id: int,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        query = self._apply_relations(
            select(Location).where(
                Location.city_id == city_id,
                Location.slug == slug.strip().lower(),
            ),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_slug(
        self,
        slug: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        query = self._apply_relations(
            select(Location).where(
                Location.slug == slug.strip().lower(),
            ),
            with_relations,
            self._relation_map,
        )
        if with_relations and with_relations.get("city"):
            query = self._with_city_country(query)
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Optional[Location]:
        query = self._apply_relations(
            select(Location).where(Location.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        if with_relations and with_relations.get("city"):
            query = self._with_city_country(query)
        return await self._fetch_one(query, flush=flush)

    async def get_by_id_with_city_country(
        self,
        location_id: int,
        flush: bool = False,
    ) -> Optional[Location]:
        query = (
            select(Location)
            .where(Location.id == location_id)
            .options(
                selectinload(Location.city).selectinload(City.country)
            )
        )
        return await self._fetch_one(query, flush=flush)

    async def update(
        self,
        location: Location,
        with_relations: Optional[WithRelations] = None,
        commit: bool = True,
    ) -> Location:
        if not commit:
            return location

        await self.db.commit()

        if with_relations:
            query = self._apply_relations(
                select(Location).where(Location.id == location.id),
                with_relations,
                self._relation_map,
            )
            if with_relations.get("city"):
                query = self._with_city_country(query)
            return await self._fetch_one(query)

        await self.db.refresh(location)
        return location


    async def list(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        filters: Optional[list[dict[str, str]]] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations: Optional[WithRelations] = None,
        flush: bool = False,
    ) -> Page[Location]:
        sort_col = getattr(Location, sort_by, Location.created_at)
        if str(sort_order).lower() == "asc":
            query = select(Location).order_by(sort_col.asc())
        else:
            query = select(Location).order_by(sort_col.desc())

        # Extract name filter if present to do case-insensitive substring matching on Location.name
        name_filter = None
        remaining_filters = []
        if filters:
            for f in filters:
                if isinstance(f, dict) and f.get("name") == "name":
                    name_filter = f.get("value")
                elif hasattr(f, "name") and getattr(f, "name") == "name":
                    name_filter = getattr(f, "value")
                else:
                    remaining_filters.append(f)

        if name_filter:
            query = query.where(Location.name.ilike(f"%{str(name_filter).strip()}%"))

        query = self._apply_search(query, search, search_fields=[Location.name, Location.slug, Location.city_id])
        query = self._apply_dynamic_filters(query, remaining_filters, self._filter_map)
        query = self._apply_relations(query, with_relations, self._relation_map)
        if with_relations and with_relations.get("city"):
            query = self._with_city_country(query)

        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def get_all_by_city_id(self, city_id: int) -> list[Location]:
        query = select(Location).where(Location.city_id == city_id)
        return await self._fetch_all(query)

