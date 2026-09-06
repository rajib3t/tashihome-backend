import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.dto.setting import SettingUpdateDTO
from app.application.use_case.admin.settings.get_setting_use_case import GetSettingUseCase
from app.application.use_case.admin.settings.update_setting_use_case import UpdateSettingUseCase
from app.models.setting_model import Setting
from app.models.user_model import User, UserRole


@pytest.fixture
def mock_admin():
    return User(id=1, email="admin@tashihomes.in", role=UserRole.ADMIN)


@pytest.fixture
def mock_setting_service():
    return MagicMock()


@pytest.fixture
def mock_storage_service():
    storage = MagicMock()
    storage.get_display_url = AsyncMock(side_effect=lambda v: f"https://cdn.tashihomes.in/{v}" if v else None)
    return storage


@pytest.mark.asyncio
async def test_update_platform_settings(mock_setting_service, mock_storage_service, mock_admin):
    saved_settings = {}

    async def mock_upsert(key, value):
        saved_settings[key] = value
        return Setting(key=key, value=value)

    async def mock_get_all():
        return [Setting(key=k, value=v) for k, v in saved_settings.items()]

    mock_setting_service.upsert = AsyncMock(side_effect=mock_upsert)
    mock_setting_service.get_all = AsyncMock(side_effect=mock_get_all)

    use_case = UpdateSettingUseCase(
        setting_service=mock_setting_service,
        storage_service=mock_storage_service,
        current_user=mock_admin,
    )

    dto = SettingUpdateDTO(
        app_name="Tashi Homestays",
        default_currency="INR",
        currency_symbol="₹",
        contact_email="support@tashihomes.in",
        contact_phone="+919876543210",
        default_commission_percentage=10.0,
        service_fee_percentage=2.5,
        check_in_time="14:00",
        check_out_time="11:00",
        min_booking_days=1,
        max_booking_days=30,
        facebook_url="https://facebook.com/tashihomes",
        meta_title="Tashi Homes - Luxury Homestays",
        is_enabled_coming_soon=False,
    )

    response = await use_case.execute(dto)

    assert saved_settings["app_name"] == "Tashi Homestays"
    assert saved_settings["default_currency"] == "INR"
    assert saved_settings["contact_email"] == "support@tashihomes.in"
    assert saved_settings["default_commission_percentage"] == 10.0
    assert saved_settings["is_enabled_coming_soon"] == "false"
    assert len(response) > 0


@pytest.mark.asyncio
async def test_get_settings_coming_soon_filtering(mock_setting_service, mock_storage_service):
    settings_data = [
        Setting(key="app_name", value="Tashi Homes"),
        Setting(key="is_enabled_coming_soon", value="false"),
        Setting(key="coming_soon_message", value="Launching soon!"),
        Setting(key="app_logo", value="settings/logo.png"),
    ]
    mock_setting_service.get_all = AsyncMock(return_value=settings_data)

    use_case = GetSettingUseCase(mock_setting_service, mock_storage_service)
    result = await use_case.execute()

    result_keys = {item.name for item in result}
    assert "app_name" in result_keys
    assert "app_logo" in result_keys
    # coming_soon_message should be filtered when is_enabled_coming_soon is false
    assert "coming_soon_message" not in result_keys

    # Check that logo URL was resolved
    logo_item = next(item for item in result if item.name == "app_logo")
    assert logo_item.value == "https://cdn.tashihomes.in/settings/logo.png"

