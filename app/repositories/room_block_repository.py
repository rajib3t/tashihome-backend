from datetime import date
from typing import Optional

from sqlalchemy import and_, func, select

from app.models.room_block_model import RoomBlock
from app.repositories.base_repository import BaseRepository


class RoomBlockRepository(BaseRepository[RoomBlock]):
    async def create(self, room_block: RoomBlock, commit: bool = True) -> RoomBlock:
        self.db.add(room_block)
        if commit:
            await self.db.commit()
            await self.db.refresh(room_block)
        return room_block

    async def get_by_id(self, block_id: int, flush: bool = False) -> Optional[RoomBlock]:
        query = select(RoomBlock).where(RoomBlock.id == block_id)
        return await self._fetch_one(query, flush=flush)

    async def count_blocked_units(
        self,
        property_id: int,
        room_type_id: Optional[int],
        check_in_date: date,
        check_out_date: date,
    ) -> int:
        """
        Count blocked units overlapping with the requested date range.
        Condition: block_start_date < check_out_date AND block_end_date > check_in_date.
        """
        query = select(func.coalesce(func.sum(RoomBlock.units_blocked), 0)).where(
            and_(
                RoomBlock.property_id == property_id,
                RoomBlock.block_start_date < check_out_date,
                RoomBlock.block_end_date > check_in_date,
            )
        )

        if room_type_id is not None:
            query = query.where(RoomBlock.room_type_id == room_type_id)

        result = await self.db.execute(query)
        return int(result.scalar_one())

