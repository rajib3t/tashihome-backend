import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_case.admin.vendors.update_vendor_use_case import UploadVendorProfileImageUseCase


def test_upload_vendor_profile_image_rolls_back_s3_when_db_update_fails():
    async def run_test():
        user_service = AsyncMock()
        user_service.get_user_by_public_id.return_value = MagicMock(
            id=1,
            role="vendor",
            is_profile_image_url="old-profile.jpg",
            company=None,
        )
        user_service.update.side_effect = Exception("db failed")

        storage_service = MagicMock()
        storage_service.convert_and_upload_webp = AsyncMock(return_value="vendor_profiles/profile_123.webp")
        storage_service.delete_object = AsyncMock()

        use_case = UploadVendorProfileImageUseCase(
            user_service=user_service,
            storage_service=storage_service,
            verify_csrf=False,
            current_user=MagicMock(),
        )

        upload = MagicMock()
        upload.read = AsyncMock(return_value=b"fake-image-bytes")
        upload.content_type = "image/jpeg"
        upload.filename = "vendor.jpg"

        with pytest.raises(Exception, match="db failed"):
            await use_case.execute("public-id", upload)

        assert storage_service.delete_object.await_args_list == [
            (("vendor_profiles/profile_123.webp",), {}),
        ]

    asyncio.run(run_test())
