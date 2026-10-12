from dataclasses import dataclass
from typing import Self

from app.core.flow.handles.base import Handle, HandlePosition, HandleType


@dataclass
class OutputHandle(Handle):
    """The output handle of a node."""

    position: HandlePosition = "right"
    is_snapshot: bool = False

    def _handle_type(self) -> HandleType:
        return "source"

    def with_loop(self, loop_id: str) -> Self:
        """Create a new output handle with the given loop node ID.

        Args:
            loop_id: Loop node ID.

        Returns:
            New output handle.
        """
        return self.create(self.id, loop_id)

    @property
    def snapshot(self) -> dict:
        """Create a snapshot dict of the output handle.

        Returns:
            Snapshot dict.
        """
        return {
            "id": self.id,
            "loop_id": self.loop_id,
            "from_snapshot": self.is_snapshot,
        }

    @classmethod
    def from_snapshot(cls, snapshot: dict | None) -> Self | None:
        """Create a new output handle from the snapshot dict.

        Args:
            snapshot: Snapshot dict.

        Returns:
            New output handle.
        """
        if snapshot is None:
            return None
        handle = cls.create(snapshot["id"], snapshot["loop_id"])
        handle.is_snapshot = True
        return handle
