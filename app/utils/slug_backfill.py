from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city_model import City
from app.models.country_model import Country
from app.models.location_model import Location
from app.utils.slug import generate_slug, generate_unique_slug


async def populate_existing_slugs(session: AsyncSession) -> dict[str, int]:
    """
    Backfill / populate slugs for existing Country, City, and Location records that have empty or NULL slugs.

    Returns a dict with count of updated records:
    {"countries": X, "cities": Y, "locations": Z}
    """
    stats = {"countries": 0, "cities": 0, "locations": 0}

    # 1. Countries (globally unique slug)
    country_stmt = select(Country).where(or_(Country.slug.is_(None), Country.slug == ""))
    country_res = await session.execute(country_stmt)
    countries = country_res.scalars().all()

    for country in countries:
        base_slug = await generate_slug(country.name)
        if not base_slug:
            base_slug = f"country-{country.id}"

        async def is_country_slug_taken(candidate: str) -> bool:
            stmt = select(Country.id).where(Country.slug == candidate, Country.id != country.id)
            res = await session.execute(stmt)
            return res.first() is not None

        country.slug = await generate_unique_slug(base_slug, is_country_slug_taken)
        stats["countries"] += 1

    # 2. Cities (globally unique slug)
    city_stmt = select(City).where(or_(City.slug.is_(None), City.slug == ""))
    city_res = await session.execute(city_stmt)
    cities = city_res.scalars().all()

    for city in cities:
        base_slug = await generate_slug(city.name)
        if not base_slug:
            base_slug = f"city-{city.id}"

        async def is_city_slug_taken(candidate: str) -> bool:
            stmt = select(City.id).where(City.slug == candidate, City.id != city.id)
            res = await session.execute(stmt)
            return res.first() is not None

        city.slug = await generate_unique_slug(base_slug, is_city_slug_taken)
        stats["cities"] += 1

    # 3. Locations (unique per city_id)
    loc_stmt = select(Location).where(or_(Location.slug.is_(None), Location.slug == ""))
    loc_res = await session.execute(loc_stmt)
    locations = loc_res.scalars().all()

    for loc in locations:
        base_slug = await generate_slug(loc.name)
        if not base_slug:
            base_slug = f"location-{loc.id}"

        async def is_loc_slug_taken(candidate: str) -> bool:
            stmt = select(Location.id).where(
                Location.slug == candidate,
                Location.city_id == loc.city_id,
                Location.id != loc.id,
            )
            res = await session.execute(stmt)
            return res.first() is not None

        loc.slug = await generate_unique_slug(base_slug, is_loc_slug_taken)
        stats["locations"] += 1

    await session.commit()
    return stats

