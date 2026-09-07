"""add slug to country city and location

Revision ID: a8b9c0d1e2f3
Revises: e5f6a7b8c9d0
Create Date: 2026-09-07 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a8b9c0d1e2f3'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


import re
import unicodedata

def _slugify(text: str) -> str:
    if not text:
        return ""
    slug = unicodedata.normalize('NFKD', text)
    slug = slug.encode('ascii', 'ignore').decode('ascii').lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-{2,}', '-', slug)
    return slug.strip('-')


def upgrade() -> None:
    """Upgrade schema and backfill slugs for existing records."""
    conn = op.get_bind()

    # 1. Countries
    op.add_column('countries', sa.Column('slug', sa.String(length=255), nullable=True))
    countries = conn.execute(sa.text("SELECT id, name FROM countries WHERE slug IS NULL OR slug = ''")).fetchall()
    for row in countries:
        c_id, c_name = row[0], row[1]
        base = _slugify(c_name) or f"country-{c_id}"
        slug = base
        suffix = 2
        while conn.execute(sa.text("SELECT id FROM countries WHERE slug = :slug AND id != :id"), {"slug": slug, "id": c_id}).first():
            slug = f"{base}-{suffix}"
            suffix += 1
        conn.execute(sa.text("UPDATE countries SET slug = :slug WHERE id = :id"), {"slug": slug, "id": c_id})
    op.create_index(op.f('ix_countries_slug'), 'countries', ['slug'], unique=True)

    # 2. Cities
    op.add_column('cities', sa.Column('slug', sa.String(length=255), nullable=True))
    cities = conn.execute(sa.text("SELECT id, name FROM cities WHERE slug IS NULL OR slug = ''")).fetchall()
    for row in cities:
        c_id, c_name = row[0], row[1]
        base = _slugify(c_name) or f"city-{c_id}"
        slug = base
        suffix = 2
        while conn.execute(sa.text("SELECT id FROM cities WHERE slug = :slug AND id != :id"), {"slug": slug, "id": c_id}).first():
            slug = f"{base}-{suffix}"
            suffix += 1
        conn.execute(sa.text("UPDATE cities SET slug = :slug WHERE id = :id"), {"slug": slug, "id": c_id})
    op.create_index(op.f('ix_cities_slug'), 'cities', ['slug'], unique=True)

    # 3. Locations
    op.add_column('locations', sa.Column('slug', sa.String(length=255), nullable=True))
    locations = conn.execute(sa.text("SELECT id, name, city_id FROM locations WHERE slug IS NULL OR slug = ''")).fetchall()
    for row in locations:
        l_id, l_name, city_id = row[0], row[1], row[2]
        base = _slugify(l_name) or f"location-{l_id}"
        slug = base
        suffix = 2
        while conn.execute(sa.text("SELECT id FROM locations WHERE slug = :slug AND city_id = :city_id AND id != :id"), {"slug": slug, "city_id": city_id, "id": l_id}).first():
            slug = f"{base}-{suffix}"
            suffix += 1
        conn.execute(sa.text("UPDATE locations SET slug = :slug WHERE id = :id"), {"slug": slug, "id": l_id})
    op.create_index(op.f('ix_locations_slug'), 'locations', ['slug'], unique=False)
    op.create_unique_constraint('uq_location_city_slug', 'locations', ['city_id', 'slug'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('uq_location_city_slug', 'locations', type_='unique')
    op.drop_index(op.f('ix_locations_slug'), table_name='locations')
    op.drop_column('locations', 'slug')

    op.drop_index(op.f('ix_cities_slug'), table_name='cities')
    op.drop_column('cities', 'slug')

    op.drop_index(op.f('ix_countries_slug'), table_name='countries')
    op.drop_column('countries', 'slug')

