import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.use_case.admin.properties.upload_property_assets_use_case import DeletePropertyAssetUseCase
from app.core.exceptions import AppException
from app.models.property_asset_model import PropertyAsset
from app.models.property_model import Property


def test_delete_property_asset_success():
    async def run_test():
        property_public_id = str(uuid.uuid4())
        asset_public_id = str(uuid.uuid4())

        property_mock = MagicMock(spec=Property)
        property_mock.id = 42
        property_mock.public_id = property_public_id

        asset_mock = MagicMock(spec=PropertyAsset)
        asset_mock.id = 100
        asset_mock.public_id = asset_public_id
        asset_mock.property_id = 42  # Integer ID matching property_.id
        asset_mock.file_url = "properties/123/asset.webp"

        property_service = AsyncMock()
        property_service.get_by_public_id.return_value = property_mock

        property_asset_service = AsyncMock()
        property_asset_service.get_by_public_id.return_value = asset_mock
        property_asset_service.delete = AsyncMock()

        storage_service = AsyncMock()
        storage_service.delete_object = AsyncMock()

        current_user = MagicMock()

        use_case = DeletePropertyAssetUseCase(
            property_service=property_service,
            property_asset_service=property_asset_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        # Mock serialize_property to return dummy serialized property dict
        use_case.serialize_property = AsyncMock(return_value={"id": property_public_id})

        res = await use_case.execute(property_id=property_public_id, asset_id=asset_public_id)

        property_service.get_by_public_id.assert_any_call(property_public_id, flush=True)
        property_asset_service.get_by_public_id.assert_called_once_with(asset_public_id, flush=True)
        storage_service.delete_object.assert_called_once_with("properties/123/asset.webp")
        property_asset_service.delete.assert_called_once_with(asset_mock, commit=True)
        assert res == {"id": property_public_id}

    asyncio.run(run_test())


def test_delete_property_asset_mismatched_property():
    async def run_test():
        property_public_id = str(uuid.uuid4())
        asset_public_id = str(uuid.uuid4())

        property_mock = MagicMock(spec=Property)
        property_mock.id = 42
        property_mock.public_id = property_public_id

        asset_mock = MagicMock(spec=PropertyAsset)
        asset_mock.id = 100
        asset_mock.public_id = asset_public_id
        asset_mock.property_id = 999  # Does NOT match property_mock.id (42)

        property_service = AsyncMock()
        property_service.get_by_public_id.return_value = property_mock

        property_asset_service = AsyncMock()
        property_asset_service.get_by_public_id.return_value = asset_mock

        storage_service = AsyncMock()
        current_user = MagicMock()

        use_case = DeletePropertyAssetUseCase(
            property_service=property_service,
            property_asset_service=property_asset_service,
            storage_service=storage_service,
            current_user=current_user,
        )

        with pytest.raises(AppException) as exc_info:
            await use_case.execute(property_id=property_public_id, asset_id=asset_public_id)

        assert exc_info.value.status_code == 403
        assert "not authorized to delete this property asset" in exc_info.value.message

    asyncio.run(run_test())
