"""Share content errors, source snapshots and limits."""

from pydantic import BaseModel, ConfigDict, Field

# bound serialized indexes without limiting cached body size
INDEX_BYTES = 8 * 1024 * 1024


class ContentError(ValueError):
    """Carry a stable content error without coupling parsers to HTTP."""

    def __init__(self, code: str):
        """Store the error code for the caller's indexing or response handling.

        Args:
            code: The stable content failure code.
        """
        super().__init__(code)
        self.code = code


class FileSnapshot(BaseModel):
    """Keep source size and modification time independently of its path."""

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    size: int = Field(ge=0)
    mtime_ns: int
