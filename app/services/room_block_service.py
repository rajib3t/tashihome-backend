from datetime import date
from typing import Optional

from app.core.exceptions import AppException
from app.models.room_block_model import RoomBlock
from app.repositories.base_repository import Page
from app.repositories.booking_repository import BookingRepository
from app.repositories.property_repository import PropertyRepository
from app.repositories.property_room_type_repository import PropertyRoomTypeRepository
from app.repositories.room_block_repository import RoomBlockRepository, RoomBlockWithRelations


class RoomBlockService:
    def __init__(
        self,
        room_block_repository: RoomBlockRepository,
        property_repository: PropertyRepository,
        property_room_type_repository: PropertyRoomTypeRepository,
        booking_repository: BookingRepository,
    ):
        self.room_block_repository = room_block_repository
        self.property_repository = property_repository
        self.property_room_type_repository = property_room_type_repository
        self.booking_repository = booking_repository

    async def get_total_units(self, property_id: int, room_type_id: int) -> int:
        prop_room_type = await self.property_room_type_repository.get_by_property_and_room_type(
            property_id, room_type_id
        )
        if prop_room_type and prop_room_type.total_units:
            return prop_room_type.total_units
        return 1

    async def validate_and_check_capacity(
        self,
        property_id: int,
        room_type_id: int,
        block_start_date: date,
        block_end_date: date,
        units_to_block: int,
        exclude_block_id: Optional[int] = None,
    ) -> None:
        """
        Validates inventory capacity so room blocks cannot exceed configured total units
        or clash with existing confirmed bookings or other active blocks.
        """
        total_units = await self.get_total_units(property_id, room_type_id)

        if units_to_block > total_units:
            raise AppException(
                status_code=400,
                message=f"Cannot block {units_to_block} unit(s). This property room type only has {total_units} total unit(s).",
                error_code="UNITS_EXCEED_TOTAL",
                field="units_blocked",
            )

        booked_units = await self.booking_repository.count_booked_units(
            property_id=property_id,
            room_type_id=room_type_id,
            check_in_date=block_start_date,
            check_out_date=block_end_date,
        )

        other_blocked_units = await self.room_block_repository.count_blocked_units(
            property_id=property_id,
            room_type_id=room_type_id,
            check_in_date=block_start_date,
            check_out_date=block_end_date,
            exclude_block_id=exclude_block_id,
        )

        available_to_block = max(0, total_units - (booked_units + other_blocked_units))

        if units_to_block > available_to_block:
            raise AppException(
                status_code=400,
                message=(
                    f"Cannot block {units_to_block} unit(s) for the selected dates. "
                    f"Total units: {total_units}, booked: {booked_units}, already blocked: {other_blocked_units}. "
                    f"Available to block: {available_to_block}."
                ),
                error_code="INSUFFICIENT_UNITS_AVAILABLE",
                field="units_blocked",
            )

    async def create(
        self,
        room_block: RoomBlock,
        with_relations: Optional[RoomBlockWithRelations] = None,
        commit: bool = True,
    ) -> RoomBlock:
        return await self.room_block_repository.create(
            room_block=room_block,
            with_relations=with_relations,
            commit=commit,
        )

    async def get_by_id(
        self,
        block_id: int,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        return await self.room_block_repository.get_by_id(
            block_id=block_id,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_by_public_id(
        self,
        public_id: str,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        return await self.room_block_repository.get_by_public_id(
            public_id=public_id,
            with_relations=with_relations,
            flush=flush,
        )

    async def get_by_identifier(
        self,
        identifier: str,
        with_relations: Optional[RoomBlockWithRelations] = None,
        flush: bool = False,
    ) -> Optional[RoomBlock]:
        return await self.room_block_repository.get_by_identifier(
            identifier=identifier,
            with_relations=with_relations,
            flush=flush,
        )

    async def update(
        self,
        room_block: RoomBlock,
        with_relations: Optional[RoomBlockWithRelations] = None,
        commit: bool = True,
    ) -> RoomBlock:
        return await self.room_block_repository.update(
            room_block=room_block,
            with_relations=with_relations,
            commit=commit,
        )

    async def delete(
        self,
        room_block: RoomBlock,
        commit: bool = True,
    ) -> None:
        await self.room_block_repository.delete(room_block=room_block, commit=commit)

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
        return await self.room_block_repository.list_vendor_room_blocks(
            vendor_id=vendor_id,
            page=page,
            page_size=page_size,
            property_id=property_id,
            room_type_id=room_type_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )

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
        return await self.room_block_repository.list_all_room_blocks(
            page=page,
            page_size=page_size,
            property_id=property_id,
            room_type_id=room_type_id,
            start_date=start_date,
            end_date=end_date,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            with_relations=with_relations,
            flush=flush,
        )

