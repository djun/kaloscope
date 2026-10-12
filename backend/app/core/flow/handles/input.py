from dataclasses import dataclass
from typing import Any

from app.core.flow.handles.base import Handle, HandlePosition, HandleType


@dataclass
class InputHandle(Handle):
    """The input handle of a node."""

    position: HandlePosition = "left"

    def _handle_type(self) -> HandleType:
        return "target"

    def __eq__(self, other: Any) -> bool:
        """Check if the given handle is equal to this handle.

        Args:
            other: Handle to compare.

        Returns:
            True if the given handle is equal to this handle, False otherwise.
        """
        if not isinstance(other, InputHandle):
            return False
        return self.id == other.id
