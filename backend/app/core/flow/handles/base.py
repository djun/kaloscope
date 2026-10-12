from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Literal, Self

type HandleType = Literal["target", "source"]
type HandlePosition = Literal["left", "top", "right", "bottom"]


@dataclass(kw_only=True)
class Handle(ABC):
    """Base definition for node handles."""

    id: str = field(init=False, repr=False)
    handle_type: HandleType = field(init=False, repr=False)
    position: HandlePosition = field(kw_only=False)
    maxconn: int | None = None
    style: str | None = None
    tag: str | None = None
    # the bound loop node ID
    loop_id: str | None = field(init=False, repr=False, default=None)

    def __post_init__(self):
        self.handle_type = self._handle_type()
        # limit handle connections to the range 1 to 20
        if self.maxconn is not None:
            self.maxconn = max(1, min(self.maxconn, 20))
        elif self.handle_type == "target":
            self.maxconn = 1
        elif self.handle_type == "source":
            self.maxconn = 20

    @abstractmethod
    def _handle_type(self) -> HandleType:
        """The method to be implemented by the subclasses to return the handle type.

        Returns:
            Handle type.
        """
        raise NotImplementedError

    @classmethod
    def create(cls, id: str, loop_id: str | None = None) -> Self:
        """Create a new handle instance.

        Args:
            id: Handle ID.
            loop_id: Loop node ID. `None` means no active loop.

        Returns:
            New handle instance.
        """
        handle = cls.__new__(cls)
        handle.__post_init__()
        handle.id = id
        handle.loop_id = loop_id
        return handle
