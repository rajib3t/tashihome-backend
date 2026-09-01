import asyncio
from datetime import date, timedelta
import unittest
from unittest.mock import AsyncMock, MagicMock
import uuid

from app.application.dto.bookings.booking import BookingAvailabilityDTO
from app.application.dto.room_blocks.room_block import (
    RoomBlockCreateDTO,
    RoomBlockQueryDTO,
    RoomBlockUpdateDTO,
)
from app.application.use_case.user.booking.check_availability_use_case import CheckAvailabilityUseCase
from app.application.use_case.vendor.room_block.create_room_block_use_case import VendorCreateRoomBlockUseCase
from app.application.use_case.vendor.room_block.delete_room_block_use_case import VendorDeleteRoomBlockUseCase
from app.application.use_case.vendor.room_block.get_room_block_detail_use_case import VendorGetRoomBlockDetailUseCase
from app.application.use_case.vendor.room_block.get_room_blocks_use_case import VendorGetRoomBlocksUseCase
from app.application.use_case.vendor.room_block.update_room_block_use_case import VendorUpdateRoomBlockUseCase
from app.core.exceptions import AppException
from app.models.property_model import Property
from app.models.property_room_type_model import PropertyRoomType
from app.models.room_block_model import RoomBlock
from app.models.room_type_model import RoomType


class TestRoomBlockUseCases(unittest.TestCase):
    def setUp(self):
        self.vendor_user = MagicMock()
        self.vendor_user.id = 10
        self.vendor_user.role = "vendor"

        self.other_vendor_user = MagicMock()
        self.other_vendor_user.id = 99
        self.other_vendor_user.role = "vendor"

    def test_vendor_create_room_block_success(self):
        async def run_test():
            prop_uuid = str(uuid.uuid4())
            rt_uuid = str(uuid.uuid4())

            property_mock = MagicMock(spec=Property)
            property_mock.id = 1
            property_mock.vendor_id = 10
            property_mock.public_id = prop_uuid

            room_type_mock = MagicMock(spec=RoomType)
            room_type_mock.id = 5
            room_type_mock.public_id = rt_uuid

            prop_rt_mock = MagicMock(spec=PropertyRoomType)
            prop_rt_mock.id = 20
            prop_rt_mock.total_units = 3

            room_block_service = AsyncMock()
            room_block_service.validate_and_check_capacity = AsyncMock()
            
            created_block_mock = MagicMock(spec=RoomBlock)
            room_block_service.create.return_value = created_block_mock

            property_service = AsyncMock()
            property_service.get_by_public_id.return_value = property_mock

            room_type_service = AsyncMock()
            room_type_service.get_by_public_id.return_value = room_type_mock

            property_room_type_service = AsyncMock()
            property_room_type_service.get_by_property_and_room_type.return_value = prop_rt_mock

            use_case = VendorCreateRoomBlockUseCase(
                room_block_service=room_block_service,
                property_service=property_service,
                room_type_service=room_type_service,
                property_room_type_service=property_room_type_service,
                current_user=self.vendor_user,
            )

            start = date.today() + timedelta(days=5)
            end = date.today() + timedelta(days=10)

            dto = RoomBlockCreateDTO(
                property_id=prop_uuid,
                room_type_id=rt_uuid,
                block_start_date=start,
                block_end_date=end,
                units_blocked=2,
                reason="Scheduled painting",
            )

            result = await use_case.execute(dto)

            room_block_service.validate_and_check_capacity.assert_called_once_with(
                property_id=1,
                room_type_id=5,
                block_start_date=start,
                block_end_date=end,
                units_to_block=2,
            )
            room_block_service.create.assert_called_once()
            self.assertEqual(result, created_block_mock)

        asyncio.run(run_test())

    def test_vendor_create_room_block_past_date(self):
        async def run_test():
            use_case = VendorCreateRoomBlockUseCase(
                room_block_service=AsyncMock(),
                property_service=AsyncMock(),
                room_type_service=AsyncMock(),
                property_room_type_service=AsyncMock(),
                current_user=self.vendor_user,
            )

            dto = RoomBlockCreateDTO(
                property_id=str(uuid.uuid4()),
                room_type_id=str(uuid.uuid4()),
                block_start_date=date.today() - timedelta(days=2),
                block_end_date=date.today() + timedelta(days=5),
                units_blocked=1,
            )

            with self.assertRaises(AppException) as ctx:
                await use_case.execute(dto)
            self.assertEqual(ctx.exception.status_code, 400)
            self.assertIn("past", ctx.exception.message)

        asyncio.run(run_test())

    def test_vendor_create_room_block_property_forbidden(self):
        async def run_test():
            prop_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.id = 1
            property_mock.vendor_id = 99  # owned by another vendor

            property_service = AsyncMock()
            property_service.get_by_public_id.return_value = property_mock

            use_case = VendorCreateRoomBlockUseCase(
                room_block_service=AsyncMock(),
                property_service=property_service,
                room_type_service=AsyncMock(),
                property_room_type_service=AsyncMock(),
                current_user=self.vendor_user,  # id = 10
            )

            dto = RoomBlockCreateDTO(
                property_id=prop_uuid,
                room_type_id=str(uuid.uuid4()),
                block_start_date=date.today() + timedelta(days=1),
                block_end_date=date.today() + timedelta(days=5),
                units_blocked=1,
            )

            with self.assertRaises(AppException) as ctx:
                await use_case.execute(dto)
            self.assertEqual(ctx.exception.status_code, 403)

        asyncio.run(run_test())

    def test_vendor_get_room_block_detail_success(self):
        async def run_test():
            block_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.vendor_id = 10

            block_mock = MagicMock(spec=RoomBlock)
            block_mock.id = 101
            block_mock.public_id = block_uuid
            block_mock.property = property_mock

            room_block_service = AsyncMock()
            room_block_service.get_by_identifier.return_value = block_mock

            use_case = VendorGetRoomBlockDetailUseCase(
                room_block_service=room_block_service,
                current_user=self.vendor_user,
            )

            res = await use_case.execute(block_uuid)
            self.assertEqual(res, block_mock)

        asyncio.run(run_test())

    def test_vendor_get_room_block_detail_forbidden(self):
        async def run_test():
            block_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.vendor_id = 99  # Not self.vendor_user (10)

            block_mock = MagicMock(spec=RoomBlock)
            block_mock.id = 101
            block_mock.public_id = block_uuid
            block_mock.property = property_mock

            room_block_service = AsyncMock()
            room_block_service.get_by_identifier.return_value = block_mock

            use_case = VendorGetRoomBlockDetailUseCase(
                room_block_service=room_block_service,
                current_user=self.vendor_user,
            )

            with self.assertRaises(AppException) as ctx:
                await use_case.execute(block_uuid)
            self.assertEqual(ctx.exception.status_code, 403)

        asyncio.run(run_test())

    def test_vendor_update_room_block_success(self):
        async def run_test():
            block_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.vendor_id = 10

            block_mock = MagicMock(spec=RoomBlock)
            block_mock.id = 101
            block_mock.property_id = 1
            block_mock.room_type_id = 5
            block_mock.block_start_date = date.today() + timedelta(days=2)
            block_mock.block_end_date = date.today() + timedelta(days=5)
            block_mock.units_blocked = 1
            block_mock.property = property_mock

            room_block_service = AsyncMock()
            room_block_service.get_by_identifier.return_value = block_mock
            room_block_service.validate_and_check_capacity = AsyncMock()
            room_block_service.update.return_value = block_mock

            use_case = VendorUpdateRoomBlockUseCase(
                room_block_service=room_block_service,
                current_user=self.vendor_user,
            )

            new_end = date.today() + timedelta(days=8)
            dto = RoomBlockUpdateDTO(
                block_end_date=new_end,
                units_blocked=2,
                reason="Extended renovation",
            )

            res = await use_case.execute(block_uuid, dto)

            room_block_service.validate_and_check_capacity.assert_called_once_with(
                property_id=1,
                room_type_id=5,
                block_start_date=block_mock.block_start_date,
                block_end_date=new_end,
                units_to_block=2,
                exclude_block_id=101,
            )
            self.assertEqual(block_mock.reason, "Extended renovation")
            self.assertEqual(block_mock.units_blocked, 2)
            self.assertEqual(res, block_mock)

        asyncio.run(run_test())

    def test_vendor_delete_room_block_success(self):
        async def run_test():
            block_uuid = str(uuid.uuid4())
            property_mock = MagicMock(spec=Property)
            property_mock.vendor_id = 10

            block_mock = MagicMock(spec=RoomBlock)
            block_mock.id = 101
            block_mock.property = property_mock

            room_block_service = AsyncMock()
            room_block_service.get_by_identifier.return_value = block_mock
            room_block_service.delete = AsyncMock()

            use_case = VendorDeleteRoomBlockUseCase(
                room_block_service=room_block_service,
                current_user=self.vendor_user,
            )

            res = await use_case.execute(block_uuid)
            room_block_service.delete.assert_called_once_with(room_block=block_mock, commit=True)
            self.assertEqual(res, block_mock)

        asyncio.run(run_test())

    def test_customer_check_availability_blocked_room_shows_unavailable(self):
        async def run_test():
            prop_uuid = str(uuid.uuid4())
            rt_uuid = str(uuid.uuid4())

            property_mock = MagicMock(spec=Property)
            property_mock.id = 1
            property_mock.public_id = prop_uuid
            property_mock.property_room_types = []

            room_type_mock = MagicMock(spec=RoomType)
            room_type_mock.id = 5
            room_type_mock.public_id = rt_uuid

            booking_service = AsyncMock()
            # 1 unit total, 0 booked, 1 blocked => 0 available
            booking_service.check_availability.return_value = {
                "is_available": False,
                "total_units": 1,
                "booked_units": 0,
                "blocked_units": 1,
                "available_units": 0,
                "requested_rooms": 1,
                "room_types_availability": [],
            }

            property_service = AsyncMock()
            property_service.get_by_public_id.return_value = property_mock

            room_type_service = AsyncMock()
            room_type_service.get_by_public_id.return_value = room_type_mock

            use_case = CheckAvailabilityUseCase(
                booking_service=booking_service,
                property_service=property_service,
                room_type_service=room_type_service,
            )

            dto = BookingAvailabilityDTO(
                property_id=prop_uuid,
                room_type_id=rt_uuid,
                check_in_date=date.today() + timedelta(days=2),
                check_out_date=date.today() + timedelta(days=5),
                num_rooms=1,
            )

            result = await use_case.execute(dto)

            booking_service.check_availability.assert_called_once_with(
                property_id=1,
                room_type_id=5,
                check_in_date=dto.check_in_date,
                check_out_date=dto.check_out_date,
                num_rooms=1,
            )
            self.assertFalse(result["is_available"])
            self.assertEqual(result["available_units"], 0)
            self.assertEqual(result["blocked_units"], 1)

        asyncio.run(run_test())


if __name__ == "__main__":
    unittest.main()
