from datetime import date
from typing import Optional, TypedDict
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from app.models.property_model import Property
from app.models.room_block_model import RoomBlock
from app.repositories.base_repository import BaseRepository, Page


class RoomBlockWithRelations(TypedDict, total=False):
    property: bool
    room_type: bool
    creator: bool


class RoomBlockRepository(BaseRepository[RoomBlock]):
    @property
    def _relation_map(self):
        return {
            "property": selectinload(RoomBlock.property),
            "room_type": selectinload(RoomBlock.room_type),
            "creator": selectinload(RoomBlock.creator),
        }

    _filter_map = {
        "id": RoomBlock.id,
        "public_id": RoomBlock.public_id,
        "property_id": RoomBlock.property_id,
        "room_type_id": RoomBlock.room_type_id,
        "created_by": RoomBlock.created_by,
    }

    async def create(
        self,
        room_block: RoomBlock,
        with_relations: Optional[RoomBlockWithRelations] = None,
        commit: bool = True,
    ) -> RoomBlock:
        self.db.add(room_block)
        if commit:
            await self.db.commit()
            await self.db.refresh(room_block)
        if with_relations:
            query = self._apply_relations(
                select(RoomBlock).where(RoomBlock.id == room_block.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return room_block

    async def get_by_id(
        self,
        block_id: int,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        query = self._apply_relations(
            select(RoomBlock).where(RoomBlock.id == block_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_public_id(
        self,
        public_id: str | UUID,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        query = self._apply_relations(
            select(RoomBlock).where(RoomBlock.public_id == public_id),
            with_relations,
            self._relation_map,
        )
        return await self._fetch_one(query, flush=flush)

    async def get_by_identifier(
        self,
        identifier: str,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        try:
            uuid_obj = UUID(str(identifier).strip())
            return await self.get_by_public_id(
                public_id=uuid_obj,
                with_relations=with_relations,
                flush=flush,
            )
        except (ValueError, AttributeError):
            if str(identifier).strip().isdigit():
                return await self.get_by_id(
                    block_id=int(str(identifier).strip()),
                    with_relations=with_relations,
                    flush=flush,
                )
            return None

    async def update(
        self,
        room_block: RoomBlock,
        with_relations: Optional[RoomBlockWithRelations] = None,
        commit: bool = True,
    ) -> RoomBlock:
        if commit:
            await self.db.commit()
            await self.db.refresh(room_block)
        if with_relations:
            query = self._apply_relations(
                select(RoomBlock).where(RoomBlock.id == room_block.id),
                with_relations,
                self._relation_map,
            )
            reloaded = await self._fetch_one(query)
            if reloaded:
                return reloaded
        return room_block

    async def delete(self, room_block: RoomBlock, commit: bool = True) -> None:
        await self.db.delete(room_block)
        if commit:
            await self.db.commit()

    async def count_blocked_units(
        self,
        property_id: int,
        room_type_id: Optional[int],
        check_in_date: date,
        check_out_date: date,
        exclude_block_id: Optional[int] = None,
    ) -> int:
        """
        Count blocked units overlapping with the requested date range.
        Condition: block_start_date < check_out_date AND block_end_date > check_in_date.
        """
        # Treat block end date as inclusive when checking overlap with a
        # booking range [check_in_date, check_out_date). Overlap if
        # block_start_date < check_out_date AND block_end_date >= check_in_date.
        query = select(func.coalesce(func.sum(RoomBlock.units_blocked), 0)).where(
            and_(
                RoomBlock.property_id == property_id,
                RoomBlock.block_start_date < check_out_date,
                RoomBlock.block_end_date >= check_in_date,
            )
        )

        if room_type_id is not None:
            query = query.where(RoomBlock.room_type_id == room_type_id)

        if exclude_block_id is not None:
            query = query.where(RoomBlock.id != exclude_block_id)

        result = await self.db.execute(query)
        return int(result.scalar_one())

    async def list_vendor_room_blocks(
        self,
        vendor_id: int,
        page: int = 1,
        page_size: int = 10,
        property_id: Optional[int] = None,
        room_type_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Page[RoomBlock]:
        """Paginated list of room blocks scoped to a vendor's own properties."""
        query = (
            select(RoomBlock)
            .join(Property, RoomBlock.property_id == Property.id)
            .where(Property.vendor_id == vendor_id)
        )

        if property_id is not None:
            query = query.where(RoomBlock.property_id == property_id)
        if room_type_id is not None:
            query = query.where(RoomBlock.room_type_id == room_type_id)
        # Include blocks that overlap the provided date range. Treat
        # block_end_date as inclusive.
        if start_date is not None:
            query = query.where(RoomBlock.block_end_date >= start_date)
        if end_date is not None:
            query = query.where(RoomBlock.block_start_date <= end_date)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    RoomBlock.reason.ilike(search_term),
                    Property.name.ilike(search_term),
                )
            )

        sort_column = getattr(RoomBlock, sort_by, RoomBlock.created_at)
        query = query.order_by(
            sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()
        )
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)

    async def list_all_room_blocks(
        self,
        page: int = 1,
        page_size: int = 10,
        property_id: Optional[int] = None,
        room_type_id: Optional[int] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Page[RoomBlock]:
        """Paginated list of all room blocks (admin)."""
        query = select(RoomBlock).join(Property, RoomBlock.property_id == Property.id)

        if property_id is not None:
            query = query.where(RoomBlock.property_id == property_id)
        if room_type_id is not None:
            query = query.where(RoomBlock.room_type_id == room_type_id)
        # Include blocks that overlap the provided date range. Treat
        # block_end_date as inclusive.
        if start_date is not None:
            query = query.where(RoomBlock.block_end_date >= start_date)
        if end_date is not None:
            query = query.where(RoomBlock.block_start_date <= end_date)
        if search:
            search_term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    RoomBlock.reason.ilike(search_term),
                    Property.name.ilike(search_term),
                )
            )

        sort_column = getattr(RoomBlock, sort_by, RoomBlock.created_at)
        query = query.order_by(
            sort_column.asc() if sort_order.lower() == "asc" else sort_column.desc()
        )
        query = self._apply_relations(query, with_relations, self._relation_map)
        return await self._paginate(query, page=page, page_size=page_size, flush=flush)
