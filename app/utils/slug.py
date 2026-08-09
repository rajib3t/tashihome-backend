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
