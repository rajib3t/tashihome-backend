import asyncio
from unittest.mock import AsyncMock, MagicMock

from app.application.dto.vendors.vendor import VendorUpdateDTO
from app.application.use_case.admin.vendors.update_vendor_use_case import UpdateVendorUseCase


def test_update_vendor_uses_transaction_and_defers_commit():
    async def run_test():
        vendor = MagicMock(
            id=7,
            role="vendor",
            full_name="Old Name",
            email="old@example.com",
            phone="1234567890",
            company=None,
            is_profile_image_url="vendor/profile.jpg",
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = vendor
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.update.return_value = vendor
        user_service.build_vendor_response = AsyncMock(return_value=vendor)
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)

        storage_service = MagicMock()
        storage_service.generate_presigned_url.return_value = "https://example.com/profile.jpg"

        use_case = UpdateVendorUseCase(
            user_service=user_service,
            storage_service=storage_service,
            company_service=MagicMock(),
            address_service=MagicMock(),
            verify_csrf=False,
            current_user=MagicMock(),
        )

        payload = VendorUpdateDTO(
            full_name="New Name",
            email="new@example.com",
            phone="9876543210",
        )

        result = await use_case.execute("vendor-public-id", payload)

        assert result is vendor
        user_service.update.assert_awaited_once_with(
            vendor,
            with_relations={"company": True},
            commit=False,
        )
        user_service.user_repository.db.begin.assert_called_once()

    asyncio.run(run_test())


def test_update_vendor_ignores_blank_company_payload():
    async def run_test():
        vendor = MagicMock(
            id=7,
            role="vendor",
            full_name="Old Name",
            email="old@example.com",
            phone="1234567890",
            company=None,
            is_profile_image_url="vendor/profile.jpg",
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = vendor
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.update.return_value = vendor
        user_service.build_vendor_response = AsyncMock(return_value=vendor)
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(return_value=None)

        company_service = MagicMock()
        company_service.create = AsyncMock()

        storage_service = MagicMock()
        storage_service.generate_presigned_url.return_value = "https://example.com/profile.jpg"

        use_case = UpdateVendorUseCase(
            user_service=user_service,
            storage_service=storage_service,
            company_service=company_service,
            address_service=MagicMock(),
            verify_csrf=False,
            current_user=MagicMock(),
        )

        payload = VendorUpdateDTO(
            full_name="New Name",
            email="new@example.com",
            phone="9876543210",
            company={
                "name": "",
                "email": "",
                "phone": "",
                "address": {
                    "address_line1": "",
                    "address_line2": "",
                    "postal_code": "",
                    "country": "",
                },
            },
        )

        await use_case.execute("vendor-public-id", payload)

        company_service.create.assert_not_awaited()
        assert vendor.company is None

    asyncio.run(run_test())


def test_update_vendor_applies_changes_before_transaction_closes():
    async def run_test():
        vendor = MagicMock(
            id=7,
            role="vendor",
            full_name="Old Name",
            email="old@example.com",
            phone="1234567890",
            company=None,
            is_profile_image_url="vendor/profile.jpg",
        )

        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = vendor
        user_service.get_user_by_email.return_value = None
        user_service.get_user_by_phone.return_value = None
        user_service.update.return_value = vendor
        user_service.build_vendor_response = AsyncMock(return_value=vendor)
        user_service.user_repository = MagicMock()
        user_service.user_repository.db = MagicMock()
        user_service.user_repository.db.in_transaction.return_value = False
        user_service.user_repository.db.flush = AsyncMock()

        observed = {}

        async def exit_handler(*args, **kwargs):
            observed["full_name_on_exit"] = vendor.full_name
            return None

        user_service.user_repository.db.begin.return_value.__aenter__ = AsyncMock()
        user_service.user_repository.db.begin.return_value.__aexit__ = AsyncMock(side_effect=exit_handler)

        storage_service = MagicMock()
        storage_service.generate_presigned_url.return_value = "https://example.com/profile.jpg"

        use_case = UpdateVendorUseCase(
            user_service=user_service,
            storage_service=storage_service,
            company_service=MagicMock(),
            address_service=MagicMock(),
            verify_csrf=False,
            current_user=MagicMock(),
        )

        payload = VendorUpdateDTO(
            full_name="New Name",
            email="new@example.com",
            phone="9876543210",
            company={
                "name": "",
                "email": "",
                "phone": "",
                "address": {
                    "address_line1": "",
                    "address_line2": "",
                    "postal_code": "",
                    "country": "",
                },
            },
        )

        await use_case.execute("vendor-public-id", payload)

        assert observed["full_name_on_exit"] == "New Name"

    asyncio.run(run_test())
