"""Text comparison and truncation utilities."""

import re
import unicodedata


def natural_key(name: str) -> tuple:
    """Sort ASCII numbers naturally, breaking equal keys with the original text.

    Args:
        name: Text to compare after Unicode normalization and case folding.

    Returns:
        A normalized natural-sort key paired with the original text for stable ties.
    """
    parts = re.split(r"([0-9]+)", unicodedata.normalize("NFC", name).casefold())
    return tuple(
        int(part) if index % 2 else part for index, part in enumerate(parts)
    ), name


def truncate_utf8(value: str, limit: int, *, marker: str = "…") -> str:
    """Truncate text to a UTF-8 byte limit without splitting characters.

    Args:
        value: Text to truncate.
        limit: Maximum encoded length, including the truncation marker.
        marker: Suffix for truncated text; defaults to an ellipsis.
            Markers larger than the limit are also truncated at character boundaries.

    Returns:
        Original text when it fits, otherwise a bounded prefix and marker.

    Raises:
        ValueError: If the byte limit is negative.
    """
    if limit < 0:
        raise ValueError("The UTF-8 byte limit must not be negative")
    encoded = value.encode()
    if len(encoded) <= limit:
        return value
    suffix = marker.encode()[:limit].decode(errors="ignore")
    prefix = encoded[: limit - len(suffix.encode())].decode(errors="ignore")
    return prefix + suffix
