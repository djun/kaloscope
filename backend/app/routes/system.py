import sys
import tomllib
from pathlib import Path

from sanic import Blueprint, HTTPResponse, json

# path to the project's pyproject.toml (backend/pyproject.toml)
_PYPROJECT = Path(__file__).parents[2] / "pyproject.toml"

system = Blueprint("system", url_prefix="/system")


@system.get("/platform")
async def get_platform(_) -> HTTPResponse:
    """Get current platform.

    Args:
        _: Unused request.

    Returns:
        Response containing the requested data.
    """
    return json({"platform": sys.platform})


@system.get("/version")
async def get_app_version(_) -> HTTPResponse:
    """Get current application version.

    Args:
        _: Unused request.

    Returns:
        Response containing the requested data.
    """
    try:
        with open(_PYPROJECT, "rb") as f:
            data = tomllib.load(f)
        version = data["project"]["version"]
    except Exception:
        version = ""
    return json({"version": version})
