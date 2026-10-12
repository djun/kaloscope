import hashlib
from pathlib import Path

from filelock import AsyncFileLock
from sanic import Sanic, SanicException

from app.core.config import KaloscopeConfig


def notify_media_events(lib_id: int):
    """Notify the library owner after persisted events have committed.

    Standalone callers without an application leave recovery to watcher startup.

    Args:
        lib_id: Library whose pending events need to be reloaded.
    """
    try:
        shared = getattr(Sanic.get_app(), "shared_ctx", None)
    except SanicException:
        return
    changes = getattr(shared, "lib_event_changes", None)
    if changes is not None:
        changes[lib_id] = True


def library_lock(directory: str) -> AsyncFileLock:
    """Create a native file lock for the canonical library path.

    Share a lock path in `workspace/temp` across workers. Wait without blocking
    the event loop; process exit releases the OS lock.

    Args:
        directory: Library root, resolved to identify the shared lock.

    Returns:
        A new asynchronous library file lock that is not yet held.
    """
    key = hashlib.sha256(str(Path(directory).resolve()).encode()).hexdigest()
    return AsyncFileLock(
        Path(KaloscopeConfig.get_workspace("temp")) / f"library_{key}.lock",
        fallback_to_soft=False,
    )


def index_lock_path(id: int) -> Path:
    """Locate the native lock shared by index readers, builders and cleanup.

    Args:
        id: Internal media item ID.

    Returns:
        A stable lock path outside the replaceable cache directory.
    """
    return Path(KaloscopeConfig.get_workspace("temp")) / f"media_index_{id}.lock"
