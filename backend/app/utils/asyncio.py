"""Asynchronous execution utilities."""

import asyncio
from collections.abc import Callable
from contextlib import suppress


async def write_in_thread[**P, R](
    function: Callable[P, R], *args: P.args, **kwargs: P.kwargs
) -> R:
    """Run a synchronous operation and finish it before propagating cancellation.

    Waiting for the worker lets callers safely release locks or clean up files.
    Preserve cancellation even if the worker fails while the caller is waiting.

    Args:
        function: Synchronous operation to run in a worker thread.
        *args: Positional arguments passed to the operation.
        **kwargs: Keyword arguments passed to the operation.

    Returns:
        Result of the operation.

    Raises:
        asyncio.CancelledError: After the worker stops, even if it fails.
        Exception: If the operation fails before cancellation.
    """
    task = asyncio.create_task(asyncio.to_thread(function, *args, **kwargs))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError:
        # wait for the worker before releasing resources it may still use
        while not task.done():
            with suppress(asyncio.CancelledError, Exception):
                await asyncio.shield(task)
        with suppress(asyncio.CancelledError, Exception):
            task.result()
        raise
