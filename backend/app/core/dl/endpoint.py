from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field, field_validator


class Endpoint(BaseModel):
    """Define the shared HTTP endpoint of a downloader."""

    model_config = ConfigDict(str_strip_whitespace=True)
    protocol: Literal["http", "https"] = "http"
    host: str = Field(min_length=1)
    port: int = Field(ge=1, le=65535)
    path: str = ""

    @field_validator("host")
    @classmethod
    def normalize_host(cls, value: str) -> str:
        """Validate and normalize the host without URL suffixes.

        Args:
            value: Host name or IP address.

        Returns:
            Normalized host name.

        Raises:
            ValueError: If the host is empty, invalid or contains URL suffixes.
        """
        if any(character in value for character in "/@?#"):
            raise ValueError("Downloader host cannot contain URL suffixes")
        try:
            host = httpx.URL(scheme="http", host=value).host
        except httpx.InvalidURL as exc:
            raise ValueError("Invalid downloader host") from exc
        if not host:
            raise ValueError("Downloader host cannot be empty")
        return host

    @field_validator("path")
    @classmethod
    def normalize_path(cls, value: str) -> str:
        """Validate the base path and remove trailing slashes.

        Args:
            value: Endpoint path; an empty string selects the server root.

        Returns:
            Absolute base path without a trailing slash.

        Raises:
            ValueError: If a nonempty path is relative.
        """
        if value and not value.startswith("/"):
            raise ValueError("Downloader path must be absolute")
        return value.rstrip("/")

    @property
    def base_url(self) -> str:
        """Get normalized endpoint URL.

        Returns:
            Normalized endpoint URL.
        """
        return str(
            httpx.URL(
                scheme=self.protocol,
                host=self.host,
                port=self.port,
                path=self.path,
            )
        )
