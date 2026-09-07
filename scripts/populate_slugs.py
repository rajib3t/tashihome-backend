import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.database import db
from app.utils.slug_backfill import populate_existing_slugs


async def main():
    print("Connecting to database...")
    db.connect()
    try:
        async with db.async_session() as session:
            print("Populating missing slugs for countries, cities, and locations...")
            stats = await populate_existing_slugs(session)
            print("Slug backfill completed successfully:")
            print(f"  - Countries updated: {stats['countries']}")
            print(f"  - Cities updated:    {stats['cities']}")
            print(f"  - Locations updated: {stats['locations']}")
    finally:
        await db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

