"""Date and time formatting utilities."""

import datetime
from typing import Literal


def duration(
    value: float, unit: Literal["milliseconds", "seconds", "minutes"] = "milliseconds"
) -> str:
    """Convert a duration to a human-readable format.

    Args:
        value: Duration value.
        unit: Input unit; defaults to milliseconds.

    Returns:
        Human-readable duration string, e.g. "01:23:45".
    """
    match unit:
        case "milliseconds":
            d = datetime.timedelta(milliseconds=value)
        case "seconds":
            d = datetime.timedelta(seconds=value)
        case "minutes":
            d = datetime.timedelta(minutes=value)
    total_seconds = int(d.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return (f"{hours:02}:" if hours else "") + f"{minutes:02}:{seconds:02}"
