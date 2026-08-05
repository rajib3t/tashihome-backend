import re
from difflib import SequenceMatcher
from typing import Optional

def has_excessive_repeating_chars(text: str, limit: int = 3) -> bool:
    """
    Checks if there are any non-whitespace characters that repeat consecutively `limit` or more times.
    By default, limit=3 will match things like 'aaa', '!!!', 'amittt'.
    """
    if not text:
        return False
    # Matches any non-whitespace character followed by (limit - 1) or more of the same character
    pattern = re.compile(rf"([^\s])\1{{{limit-1},}}", re.IGNORECASE)
    return bool(pattern.search(text))

def find_similar_name(new_name: str, existing_names: list[str], threshold: float = 0.8) -> Optional[str]:
    """
    Checks if `new_name` is too similar to any name in `existing_names` using Levenshtein-like SequenceMatcher ratio.
    Returns the first matching similar name, or None if no name is similar.
    """
    if not new_name:
        return None
    new_name_lower = new_name.strip().lower()
    for name in existing_names:
        if not name:
            continue
        if SequenceMatcher(None, new_name_lower, name.strip().lower()).ratio() >= threshold:
            return name
    return None

def validate_name_field(value: str, field_name: str = "name", max_length: int = 50, error_code_prefix: str = "NAME") -> str:
    from app.core.exceptions import AppException
    if not value or not value.strip():
        raise AppException(
            status_code=422,
            message=f"{field_name.capitalize()} cannot be empty.",
            field=field_name,
            error_code=f"{error_code_prefix}_EMPTY",
        )
    cleaned = value.strip()
    if len(cleaned) > max_length:
        raise AppException(
            status_code=422,
            message=f"{field_name.capitalize()} must be {max_length} characters or fewer.",
            field=field_name,
            error_code=f"{error_code_prefix}_TOO_LONG",
        )
    if has_excessive_repeating_chars(cleaned):
        raise AppException(
            status_code=422,
            message=f"{field_name.capitalize()} contains too many repeating characters.",
            field=field_name,
            error_code=f"{error_code_prefix}_REPETITIVE",
        )
    return cleaned

