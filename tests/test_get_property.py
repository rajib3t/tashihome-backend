import pytest
import asyncio
from app.core.database import db, get_db_session
from app.repositories.property_repository import PropertyRepository

@pytest.mark.anyio
async def test_get_property_by_public_id():
    db.connect()
    try:
        async with get_db_session() as db_session:
            repo = PropertyRepository(db_session)
            prop = await repo.get_by_public_id(
                "1555b9b2-96d1-4091-9a89-3da4ffa6369b",
                with_relations={
                    "property_room_types": True,
                    "property_amenities": True,
                    "property_facilities": True,
                    "property_food_options": True,
                },
            )
            assert prop is not None
            assert isinstance(prop.property_facilities, list)
    finally:
        await db.disconnect()