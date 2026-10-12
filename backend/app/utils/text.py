"""Text comparison utilities."""

import re
import unicodedata


def natural_key(name: str) -> tuple:
    """Sort ASCII numbers naturally, breaking equal keys with the original text.

    Args:
        name: The text to compare after Unicode normalization and case folding.

    Returns:
        A normalized natural-sort key paired with the original text for stable ties.
    """
    parts = re.split(r"([0-9]+)", unicodedata.normalize("NFC", name).casefold())
    return tuple(
        int(part) if index % 2 else part for index, part in enumerate(parts)
    ), name
