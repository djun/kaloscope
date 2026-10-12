"""Unit tests for filesystem utilities."""

import os
from pathlib import Path
from unittest.mock import Mock

import pytest

from app.utils.disk import original_file_info


@pytest.mark.parametrize("kind", ["file", "directory", "symlink", "broken_symlink"])
def test_original_info(tmp_path, monkeypatch, kind):
    target = tmp_path / "原始.mkv"
    if kind == "directory":
        target.mkdir()
    elif kind != "broken_symlink":
        target.write_bytes(b"video")
    if target.exists():
        os.utime(target, (1_700_000_000, 1_700_000_000))
    path = target
    if "symlink" in kind:
        path = tmp_path / "link.mkv"
        path.symlink_to("./原始.mkv")
    monkeypatch.chdir(tmp_path)

    original = original_file_info(path.name)

    assert original == {
        "path": str(path),
        "type": "symlink" if kind == "broken_symlink" else kind,
        "size": 5 if kind in ("file", "symlink") else None,
        "mtime": None if kind == "broken_symlink" else "2023-11-14T22:13:20+00:00",
        "link_target": "./原始.mkv" if "symlink" in kind else None,
    }


@pytest.mark.parametrize("error", [FileNotFoundError, PermissionError])
def test_original_unavailable(tmp_path, monkeypatch, error):
    path = tmp_path / "original.mkv"

    def unavailable(self):
        """Simulate unavailable source attributes.

        Raises:
            OSError: With the selected filesystem access error.
        """
        raise error(str(self))

    monkeypatch.setattr(Path, "lstat", unavailable)

    original = original_file_info(path)

    assert original == {
        "path": str(path),
        "type": None,
        "size": None,
        "mtime": None,
        "link_target": None,
    }


@pytest.mark.parametrize("mtime", [253_402_300_800.0, -62_135_596_801.0, float("inf")])
def test_original_timestamp(tmp_path, monkeypatch, mtime):
    path = tmp_path / "source.mkv"
    path.write_bytes(b"video")
    info = list(path.stat())
    info[8] = mtime
    monkeypatch.setattr(Path, "lstat", Mock(return_value=os.stat_result(info)))

    original = original_file_info(path)

    assert original == {
        "path": str(path),
        "type": "file",
        "size": 5,
        "mtime": None,
        "link_target": None,
    }
