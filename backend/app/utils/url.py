"""URL query utilities."""

from urllib.parse import parse_qsl, urlsplit, urlunsplit


def query_param(url: str, param: str) -> str:
    """Append a query parameter to a URL if the key is not already present.

    Args:
        url: The original URL.
        param: The query parameter in `key=value` format.

    Returns:
        The URL with the query parameter appended when applicable.
    """
    if not url or not param:
        return url

    key, separator, _ = param.partition("=")
    if not separator or not key:
        return url

    parts = urlsplit(url)
    existing_params = parse_qsl(parts.query, keep_blank_values=True)
    if any(existing_key == key for existing_key, _ in existing_params):
        return url

    query = param if not parts.query else f"{parts.query}&{param}"
    return urlunsplit((parts.scheme, parts.netloc, parts.path, query, parts.fragment))
