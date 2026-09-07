import re
import unicodedata


async def generate_slug(name: str) -> str:
    """
    Generate a WordPress-style slug from a name.
    
    Converts the name to a URL-friendly slug by:
    - Converting to lowercase
    - Removing special characters and accents
    - Replacing spaces and underscores with hyphens
    - Removing multiple consecutive hyphens
    - Trimming hyphens from start and end
    
    Args:
        name: The input string to convert to slug
        
    Returns:
        A URL-friendly slug string
    """
    if not name:
        return ""
    
    # Normalize unicode characters (convert accented characters to ASCII)
    slug = unicodedata.normalize('NFKD', name)
    
    # Convert to ASCII, ignoring non-ASCII characters
    slug = slug.encode('ascii', 'ignore').decode('ascii')
    
    # Convert to lowercase
    slug = slug.lower()
    
    # Replace spaces, underscores, and special characters with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    
    # Remove any character that is not alphanumeric, hyphen, or whitespace
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-{2,}', '-', slug)
    
    # Trim hyphens from start and end
    slug = slug.strip('-')
    
    return slug


async def generate_unique_slug(base_slug: str, check_exists_fn) -> str:
    """
    WordPress-style slug uniqueness: if 'base_slug' is taken (check_exists_fn returns True/truthy),
    try 'base_slug-2', 'base_slug-3', ... until a free one is found.

    Args:
        base_slug: The base slug string.
        check_exists_fn: An async callable accepting a slug string and returning True/truthy if it exists.

    Returns:
        A unique slug string.
    """
    slug = base_slug
    suffix = 2

    while await check_exists_fn(slug):
        slug = f"{base_slug}-{suffix}"
        suffix += 1

    return slug


async def populate_existing_slugs(session) -> dict[str, int]:
    """
    Backfill / populate slugs for existing Country, City, and Location records that have empty or NULL slugs.
    """
    from app.utils.slug_backfill import populate_existing_slugs as _populate
    return await _populate(session)


