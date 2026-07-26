from sqlalchemy import select

from app.models.country_model import Country, CountryStatus
from app.repositories.base_repository import BaseRepository


def test_dynamic_filter_does_not_lower_enum_columns():
    repository = BaseRepository(db=None)

    query = select(Country)
    query = repository._apply_dynamic_filters(
        query,
        [{"name": "status", "value": CountryStatus.INACTIVE}],
        {"status": Country.status},
    )

    compiled = str(query.compile(compile_kwargs={"literal_binds": True}))

    assert "lower(countries.status)" not in compiled
    assert "countries.status" in compiled
