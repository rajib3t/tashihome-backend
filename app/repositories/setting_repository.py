from typing import Optional

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.models.setting_model import Setting
from app.repositories.base_repository import BaseRepository


class SettingRepository(BaseRepository[Setting]):

    async def get_by_key(self, key: str, flush: bool = False) -> Optional[Setting]:
        """
        Retrieve a setting by its key.

        Args:
            key (str): The key of the setting to retrieve.
            flush (bool): Whether to flush pending changes before querying.

        Returns:
            Setting | None: The setting object if found, otherwise None.
        """
        query = select(Setting).where(Setting.key == key)
        return await self._fetch_one(query, flush=flush)

    async def save(self, setting: Setting, commit: bool = True) -> Setting:
        """
        Add or update a setting in the database.

        Args:
            setting (Setting): The setting object to persist.
            commit (bool): Whether to commit the transaction immediately.

        Returns:
            Setting: The persisted setting object.
        """
        self.db.add(setting)

        if not commit:
            return setting

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

        await self.db.refresh(setting)
        return setting
    
    async def delete(self, setting: Setting, commit: bool = True) -> None:
        """
        Delete a setting from the database.

        Args:
            setting (Setting): The setting object to delete.
            commit (bool): Whether to commit the transaction immediately.
        """
        await self.db.delete(setting)

        if not commit:
            return

        try:
            await self.db.commit()
        except SQLAlchemyError:
            await self.db.rollback()
            raise

    async def get_all(self, flush: bool = False) -> list[Setting]:
        """
        Retrieve all settings from the database.

        Args:
            flush (bool): Whether to flush pending changes before querying.
        Returns:
            list[Setting]: A list of all setting objects.
        """
        query = select(Setting)
        return await self._fetch_all(query, flush=flush)
        