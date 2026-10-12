"""Filesystem metadata, disk usage and cleanup utilities."""

import ctypes
import errno
import os
import shutil
import stat
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from send2trash import send2trash

from app.core.config import KaloscopeConfig


@dataclass
class DiskUsage:
    """The disk usage statistics."""

    total: int | None = None
    used: int | None = None
    free: int | None = None

    def _format(self, size: int | None) -> str:
        """Format the disk usage size.

        Args:
            size: The size in bytes.

        Returns:
            The formatted size.
        """
        return format_bytes(size) if size is not None else ""

    def total_space(self) -> str:
        return self._format(self.total)

    def used_space(self) -> str:
        return self._format(self.used)

    def free_space(self) -> str:
        return self._format(self.free)


def disk_usage(path: Path | str) -> DiskUsage:
    """Get the disk usage of a directory.

    Args:
        path: The path to the directory.

    Returns:
        The disk usage statistics object.
    """
    if not is_directory(path):
        return DiskUsage()

    try:
        total, used, free = shutil.disk_usage(path)
        return DiskUsage(total, used, free)
    except OSError:
        return DiskUsage()


def is_directory(path: Path | str) -> bool:
    """Check if a path is a directory.

    Args:
        path: The path to check.

    Returns:
        True if the path is a directory, False otherwise.
    """
    try:
        if not isinstance(path, Path):
            path = Path(path)
        return path.is_dir()
    except OSError:
        return False


def delete_path(path: Path | str):
    """Delete a filesystem path according to filesystem trash mode.

    When filesystem trash mode is enabled, the path is moved to the OS trash.
    When disabled, files and symlinks are unlinked and directories are removed.

    Args:
        path: The file or directory path to delete.
    """
    if not isinstance(path, Path):
        path = Path(path)
    if not path.exists() and not path.is_symlink():
        return

    if KaloscopeConfig.get().filesystem_trash_mode:
        send2trash(path)
    elif path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def format_bytes(size_bytes: int) -> str:
    """Format the size in bytes to a human-readable format.

    Args:
        size_bytes: The size in bytes.

    Returns:
        The human-readable size.
    """
    if size_bytes == 0:
        return "0 B"
    i = 0
    size = float(size_bytes)
    sizes = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    while size > 1024:
        size /= 1024
        i += 1
    return f"{size:.1f}".rstrip("0").rstrip(".") + " " + sizes[i]


def rename_exclusive(source: Path, destination: Path):
    """Rename a file or directory atomically without overwriting the destination.

    Args:
        source: The file or directory to rename.
        destination: The final path, which must not already exist.

    Raises:
        OSError: If exclusive renaming is unavailable or fails.
    """
    if sys.platform == "win32":
        os.rename(source, destination)
        return

    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        rename = libc.renamex_np
        rename.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        # request `RENAME_EXCL`
        arguments = (os.fsencode(source), os.fsencode(destination), 0x4)
    elif sys.platform == "linux" and hasattr(libc, "renameat2"):
        rename = libc.renameat2
        rename.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        # use `AT_FDCWD` and `RENAME_NOREPLACE`
        arguments = (-100, os.fsencode(source), -100, os.fsencode(destination), 1)
    else:
        raise OSError(errno.ENOSYS, "Exclusive renaming is unavailable")
    rename.restype = ctypes.c_int
    if rename(*arguments) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), destination)


def original_file_info(path: str | Path) -> dict[str, Any]:
    """Capture the supplied location and filesystem attributes.

    Read only filesystem metadata and run this operation in a worker thread.
    Keep the supplied location without resolving symlinks. For symlinks, store
    the raw link target and capture the target's size and modification time.

    Args:
        path: The file or directory to inspect without resolving its location.

    Returns:
        The absolute path, entry type, regular-file size in bytes, modification
        time in UTC ISO 8601 format and raw symlink target. Unavailable attributes
        remain `None` if filesystem access or timestamp conversion fails.
        Directory sizes remain `None`.
    """
    path = Path(path).absolute()
    original: dict[str, Any] = {
        "path": str(path),
        "type": None,
        "size": None,
        "mtime": None,
        "link_target": None,
    }
    try:
        info = path.lstat()
        if stat.S_ISLNK(info.st_mode):
            original["type"] = "symlink"
            original["link_target"] = os.readlink(path)
            info = path.stat()
        elif stat.S_ISDIR(info.st_mode):
            original["type"] = "directory"
        elif stat.S_ISREG(info.st_mode):
            original["type"] = "file"
        if stat.S_ISREG(info.st_mode):
            original["size"] = info.st_size
        original["mtime"] = datetime.fromtimestamp(info.st_mtime, tz=UTC).isoformat()
    except (OSError, ValueError, OverflowError):
        pass
    return original


def file_state(info: os.stat_result) -> tuple[int, ...]:
    """Return file identity and write attributes for stability checks.

    Args:
        info: The filesystem attributes captured during a build or read.

    Returns:
        Identity, size and write timestamps, excluding access time and path.
    """
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
