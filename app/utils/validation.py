import re
from difflib import SequenceMatcher
from typing import Optional

from app.core.exceptions import AppException

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

def validate_description(
    value: Optional[str],
    required: bool = False,
    max_length: int = 512,
    field_name: str = "description",
    error_code_prefix: str = "DESCRIPTION",
) -> Optional[str]:
    """
    Validates description field to prevent XSS and code injection attacks.
    
    Prevents:
    - HTML/XML tags (script, iframe, img, style, etc.)
    - JavaScript code (eval, function, onclick, etc.)
    - Dangerous characters and patterns
    
    Args:
        value: The description text to validate
        required: Whether description is required
        max_length: Maximum allowed length (default 512)
        field_name: Field name for error reporting (default "description")
        error_code_prefix: Error code prefix (default "DESCRIPTION")
        
    Returns:
        Sanitized description text
        
    Raises:
        AppException: If description contains dangerous content
    """
    field_label = field_name.replace("_", " ").capitalize()

    if value is None:
        if required:
            raise AppException(
                status_code=422,
                message=f"{field_label} is required.",
                field=field_name,
                error_code=f"{error_code_prefix}_REQUIRED",
            )
        return value

    value = value.strip()

    if not value:
        if required:
            raise AppException(
                status_code=422,
                message=f"{field_label} is required.",
                field=field_name,
                error_code=f"{error_code_prefix}_REQUIRED",
            )
        return None

    if len(value) > max_length:
        raise AppException(
            status_code=422,
            message=f"{field_label} must not exceed {max_length} characters.",
            field=field_name,
            error_code=f"{error_code_prefix}_TOO_LONG",
        )

    # Dangerous patterns to check for (case-insensitive)
    dangerous_patterns = [
        r"<\s*script",  # <script tags
        r"<\s*iframe",  # <iframe tags
        r"<\s*img",     # <img tags
        r"<\s*style",   # <style tags
        r"<\s*link",    # <link tags
        r"<\s*meta",    # <meta tags
        r"<\s*embed",   # <embed tags
        r"<\s*object",  # <object tags
        r"on\w+\s*=",   # onclick, onerror, onload, etc.
        r"javascript\s*:",  # javascript: protocol
        r"data\s*:",    # data: protocol
        r"vbscript\s*:",  # vbscript: protocol
        r"eval\s*\(",   # eval() function
        r"expression\s*\(",  # expression() function
        r"import\s+",   # import statements
        r"exec\s*\(",   # exec() function
        r"\bfunction\b",  # function keyword
        r"<\s*\/?\s*[a-zA-Z]+",  # Any HTML tag
        r"[\<\>]",  # Any angle brackets
        r"[\{\}\[\]]",  # Any curly or square brackets
    ]

    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            raise AppException(
                status_code=422,
                message=f"{field_label} contains invalid characters.",
                field=field_name,
                error_code=f"{error_code_prefix}_INVALID",
            )

    return value