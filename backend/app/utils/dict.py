"""Dictionary helper utilities."""

from collections.abc import Callable
from multiprocessing.managers import DictProxy
from typing import Any, overload

_MISSING = object()


def entries[K, V](
    d: dict[K, V] | DictProxy[K, V],
    *,
    keys: list[K] | None = None,
    kfilter: Callable[[K], bool] | None = None,
    vfilter: Callable[[V], bool] | None = None,
) -> list[tuple[K, V]]:
    """Get entries of a dictionary.

    Args:
        d: Dictionary to get the entries from.
        keys: A list of keys to include in the result. `None` supplies no explicit key
            selection.
        kfilter: A function to filter keys. `None` adds no key filter.
        vfilter: A function to filter values. `None` adds no value filter.

    Returns:
        A list of key-value pairs that satisfy the conditions.
    """
    if keys is None and kfilter is None and vfilter is None:
        return list(d.items())
    return [
        (k, v)
        for k, v in d.items()
        if (keys is not None and k in keys)
        or (kfilter is not None and kfilter(k))
        or (vfilter is not None and vfilter(v))
    ]


def keys[K, V](
    d: dict[K, V] | DictProxy[K, V],
    *,
    keys: list[K] | None = None,
    kfilter: Callable[[K], bool] | None = None,
    vfilter: Callable[[V], bool] | None = None,
) -> list[K]:
    """Get keys of a dictionary.

    Args:
        d: Dictionary to get the keys from.
        keys: A list of keys to include in the result. `None` supplies no explicit key
            selection.
        kfilter: A function to filter keys. `None` adds no key filter.
        vfilter: A function to filter values. `None` adds no value filter.

    Returns:
        A list of keys that satisfy the conditions.
    """
    return [k for k, _ in entries(d, keys=keys, kfilter=kfilter, vfilter=vfilter)]


def values[K, V](
    d: dict[K, V] | DictProxy[K, V],
    *,
    keys: list[K] | None = None,
    kfilter: Callable[[K], bool] | None = None,
    vfilter: Callable[[V], bool] | None = None,
) -> list[V]:
    """Get values of a dictionary.

    Args:
        d: Dictionary to get the values from.
        keys: A list of keys to include in the result. `None` supplies no explicit key
            selection.
        kfilter: A function to filter keys. `None` adds no key filter.
        vfilter: A function to filter values. `None` adds no value filter.

    Returns:
        A list of values that satisfy the conditions.
    """
    return [v for _, v in entries(d, keys=keys, kfilter=kfilter, vfilter=vfilter)]


def remove[K, V](
    d: dict[K, V] | DictProxy[K, V],
    key: K | None = None,
    *,
    keys: list[K] | None = None,
    kfilter: Callable[[K], bool] | None = None,
    vfilter: Callable[[V], bool] | None = None,
):
    """Remove entries from a dictionary.

    Args:
        d: Dictionary to remove entries from.
        key: A key to remove. `None` supplies no single-key selection.
        keys: A list of keys to remove. `None` supplies no explicit key selection.
        kfilter: A function to filter keys. `None` adds no key filter.
        vfilter: A function to filter values. `None` adds no value filter.
    """
    popkeys = set()
    if key is not None:
        popkeys.add(key)
    if keys is not None:
        popkeys.update(keys)
    if kfilter is not None:
        popkeys.update(k for k, _ in entries(d, kfilter=kfilter))
    if vfilter is not None:
        popkeys.update(k for k, _ in entries(d, vfilter=vfilter))
    for k in popkeys:
        d.pop(k, None)


class TrackableDict[K, V](dict[K, V]):
    """A dictionary that tracks write attempts."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._modified = False

    def __setitem__(self, key: K, value: V):
        self._modified = True
        super().__setitem__(key, value)

    def __delitem__(self, key: K):
        self._modified = True
        super().__delitem__(key)

    def update(self, *args, **kwargs):
        self._modified = True
        super().update(*args, **kwargs)

    @overload
    def setdefault[T](
        self: "TrackableDict[K, T | None]", key: K, default: None = None
    ) -> T | None: ...

    @overload
    def setdefault(self, key: K, default: V) -> V: ...

    def setdefault(self: "TrackableDict[K, Any]", key: K, default: Any = None):
        self._modified = True
        return super().setdefault(key, default)

    @overload
    def pop(self, key: K) -> V: ...

    @overload
    def pop(self, key: K, default: V) -> V: ...

    @overload
    def pop[T](self, key: K, default: T) -> V | T: ...

    def pop(self, key: K, default=_MISSING):
        self._modified = True
        # preserve KeyError when no default was provided
        if default is _MISSING:
            return super().pop(key)
        return super().pop(key, default)

    def popitem(self):
        self._modified = True
        return super().popitem()

    def clear(self):
        self._modified = True
        super().clear()

    def is_modified(self) -> bool:
        """Check whether a write method has been called since the last reset.

        Returns:
            True after a write attempt, False otherwise.
        """
        return self._modified

    def reset_modified(self):
        """Reset the modified flag to False."""
        self._modified = False


def get_raw(dictionary: dict, key: str, default: Any = None) -> Any:
    """Get a nested dictionary value using a dot-separated key.

    Args:
        dictionary: Dictionary to get the key from.
        key: Nested key to get, separated by dots.
        default: Value returned when the key is missing; defaults to `None`.

    Returns:
        Value of the nested key, or the default value if not found.
    """
    keys = key.split(".")
    data = dictionary
    for k in keys:
        if isinstance(data, dict) and k in data:
            data = data[k]
        else:
            return default
    return data
