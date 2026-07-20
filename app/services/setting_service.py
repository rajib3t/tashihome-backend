from typing import Optional

from app.models.setting_model import Setting
from app.repositories.setting_repository import SettingRepository


class SettingNotFoundError(Exception):
    """Raised when a setting with the given key does not exist."""

    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Setting with key '{key}' not found.")


class SettingService:
    def __init__(
            self,
            setting_repository: SettingRepository
    ):
        self.setting_repository = setting_repository

    async def get_by_key(self, key: str) -> Setting:
        """
        Retrieve a setting by its key.

        Args:
            key (str): The key of the setting to retrieve.

        Returns:
            Setting: The setting object.

        Raises:
            SettingNotFoundError: If no setting exists with the given key.
        """
        setting = await self.setting_repository.get_by_key(key)
        if setting is None:
            raise SettingNotFoundError(key)
        return setting

    async def get_value(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Retrieve a setting's value by its key, returning a default if not found.

        Args:
            key (str): The key of the setting to retrieve.
            default (Optional[str]): Value to return if the setting doesn't exist.

        Returns:
            Optional[str]: The setting's value, or the default if not found.
        """
        setting = await self.setting_repository.get_by_key(key)
        return setting.value if setting else default

    async def create(self, key: str, value: str, commit: bool = True) -> Setting:
        """
        Create a new setting.

        Args:
            key (str): The key of the setting.
            value (str): The value of the setting.
            commit (bool): Whether to commit the transaction immediately.

        Returns:
            Setting: The created setting object.
        """
        setting = Setting(key=key, value=value)
        return await self.setting_repository.save(setting, commit=commit)

    async def update_value(self, key: str, value: str, commit: bool = True) -> Setting:
        """
        Update the value of an existing setting.

        Args:
            key (str): The key of the setting to update.
            value (str): The new value for the setting.
            commit (bool): Whether to commit the transaction immediately.

        Returns:
            Setting: The updated setting object.

        Raises:
            SettingNotFoundError: If no setting exists with the given key.
        """
        setting = await self.get_by_key(key)
        setting.value = value
        return await self.setting_repository.save(setting, commit=commit)

    async def upsert(self, key: str, value: str, commit: bool = True) -> Setting:
        """
        Create a setting if it doesn't exist, otherwise update its value.

        Args:
            key (str): The key of the setting.
            value (str): The value to set.
            commit (bool): Whether to commit the transaction immediately.

        Returns:
            Setting: The created or updated setting object.
        """
        setting = await self.setting_repository.get_by_key(key)
        if setting is None:
            setting = Setting(key=key, value=value)
        else:
            setting.value = value
        return await self.setting_repository.save(setting, commit=commit)


    async def delete(self, key: str, commit: bool = True) -> None:
        """
        Delete a setting by its key.

        Args:
            key (str): The key of the setting to delete.
            commit (bool): Whether to commit the transaction immediately.

        Raises:
            SettingNotFoundError: If no setting exists with the given key.
        """
        setting = await self.get_by_key(key)
        await self.setting_repository.delete(setting, commit=commit)


    async def get_all(self, flush: bool = False) -> list[Setting]:
        """
        Retrieve all settings.

        Returns:
            list[Setting]: A list of all setting objects.
        """
        return await self.setting_repository.get_all(flush=flush)