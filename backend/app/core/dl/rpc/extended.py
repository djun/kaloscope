import asyncio
import contextlib
import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
from jinja2 import TemplateError
from sanic import Sanic
from sanic.log import logger

from app.core.dl.rpc.client import RpcClient, _failed, _mapping, _successful
from app.core.dl.rpc.models import API, APIResponse, Method, RpcConfig
from app.core.exceptions import ErrorCode, KaloscopeException
from app.core.network import NetworkTransport
from app.core.renderer import jsonpath_all, jsonpath_first, render
from app.utils.json import JSONType, loads

_SKIPPED = object()


@dataclass
class _SessionState:
    """Store cached session data and coordinate concurrent refreshes."""

    data: dict = field(default_factory=dict)
    expires: float = 0
    generation: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


@dataclass(slots=True)
class ExtendedRpcClient(RpcClient):
    """Execute declarative sessions and request sequences."""

    def _session_state(self) -> _SessionState:
        """Get cached session for this worker and downloader configuration.

        Returns:
            Shared session data, expiry and refresh lock.
        """
        ctx = Sanic.get_app().ctx
        if not hasattr(ctx, "rpc_sessions"):
            ctx.rpc_sessions = {}
        key = hashlib.sha256(
            self.config.model_dump_json(by_alias=True).encode()
        ).hexdigest()
        if key not in ctx.rpc_sessions:
            # limit the number of configurations cached by this worker
            if len(ctx.rpc_sessions) >= 128:
                del ctx.rpc_sessions[next(iter(ctx.rpc_sessions))]
            ctx.rpc_sessions[key] = _SessionState()
        return ctx.rpc_sessions[key]

    async def call(self, method: Method, variables: dict | None = None) -> JSONType:
        """Call an RPC method with session and step support.

        Args:
            method: Configured RPC method.
            variables: Variables to render the API with. `None` adds no call
                variables.

        Returns:
            Processed result, or `None` if the method is missing or skipped.
        """
        api = self.config.methods.get(method)
        if api is None:
            return None
        context = dict(variables or {})
        context.update(variables=self.config.variables, steps={}, session={})
        if self.config.auth:
            context.update(
                secret=self.config.auth.secret or "",
                username=self.config.auth.username or "",
                password=self.config.auth.password or "",
            )
        state = self._session_state() if self.config.session else _SessionState()
        async with contextlib.AsyncExitStack() as stack:
            http = self.http
            if http is None:
                if self.config.unix_socket or self.config.session:
                    # bypass the shared HTTP cache for authentication and task data
                    transport = (
                        httpx.AsyncHTTPTransport(uds=self.config.unix_socket)
                        if self.config.unix_socket
                        else NetworkTransport()
                    )
                    http = await stack.enter_async_context(
                        httpx.AsyncClient(transport=transport, trust_env=False)
                    )
                else:
                    http = Sanic.get_app().ctx.httpx
            execution = _Execution(self, http, state, method)
            try:
                await execution.ensure_session()
                context["session"] = state.data
                result = await execution.execute(api, context)
                return None if result is _SKIPPED else result
            except (httpx.RequestError, TemplateError, ValueError, TypeError) as exc:
                # templates, auth pages and remote errors can contain credentials
                logger.error("RPC request failed (%s).", type(exc).__name__)
                raise KaloscopeException(ErrorCode.HTTP_REQUEST_FAILED) from None


@dataclass
class _Execution:
    """Execute one RPC method with shared step and session variables."""

    client: ExtendedRpcClient
    http: httpx.AsyncClient
    session: _SessionState
    method: Method
    requests: int = 0

    @property
    def config(self) -> RpcConfig:
        return self.client.config

    async def ensure_session(self, rejected_generation: int | None = None):
        """Reuse a valid session or refresh it after expiration or rejection.

        Concurrent calls reuse a session refreshed after their rejected request.

        Args:
            rejected_generation: Session version used by a rejected request, `None`
                initializes or reuses the current session.
                or `None` to check only the expiry.
        """
        config = self.config.session
        if not config:
            return
        async with self.session.lock:
            if time.monotonic() < self.session.expires and (
                rejected_generation is None
                or rejected_generation != self.session.generation
            ):
                return
            # isolate authentication variables from the current operation's results
            context = {"variables": self.config.variables, "steps": {}, "session": {}}
            if self.config.auth:
                context.update(self.config.auth.model_dump())
            data = await self.execute(config.request, context, bootstrap=True)
            if not isinstance(data, dict) or not data:
                raise ValueError("RPC session request must return a nonempty object")
            self.session.data = data
            self.session.expires = time.monotonic() + config.ttl
            self.session.generation += 1

    async def execute(
        self, api: API, context: dict, *, bootstrap: bool = False, depth: int = 0
    ) -> Any:
        """Execute a request or a sequence of steps.

        Args:
            api: Request or step configuration.
            context: Shared template variables and saved step results.
            bootstrap: Whether this execution is initializing a session. Defaults to
                `False`.
            depth: Current nesting depth of the steps. Defaults to `0`.

        Returns:
            Last executed result, or `_SKIPPED` if no request ran.
        """
        if depth > 16:
            raise ValueError("RPC steps exceed maximum depth")
        if not _condition(api.when, context):
            return _SKIPPED
        if not _condition(api.require, context):
            raise ValueError("RPC request requirement failed")
        result = _SKIPPED
        if api.steps:
            items = (
                render(api.foreach, context, raw=True, strict=True)
                if api.foreach is not None
                else [None]
            )
            if not isinstance(items, list) or len(items) > 256:
                raise ValueError("RPC foreach requires at most 256 items")
            previous = context.get("loop_item", _SKIPPED)
            try:
                for item in items:
                    if api.foreach is not None:
                        context["loop_item"] = item
                    for step in api.steps:
                        value = await self.execute(
                            step, context, bootstrap=bootstrap, depth=depth + 1
                        )
                        if value is not _SKIPPED:
                            result = value
                    if api.save_as and result is not _SKIPPED:
                        # make each iteration's result available to the next one
                        context["steps"][api.save_as] = result
            finally:
                # restore the outer loop variable after nested steps finish
                if previous is _SKIPPED:
                    context.pop("loop_item", None)
                else:
                    context["loop_item"] = previous
            if result is not _SKIPPED:
                result = await self.process(api.response, result, context)
        else:
            result = await self.paginate(api, context, bootstrap=bootstrap)
        if api.save_as and result is not _SKIPPED:
            context["steps"][api.save_as] = result
        return result

    async def paginate(self, api: API, context: dict, *, bootstrap: bool) -> Any:
        """Request and process responses until pagination is complete.

        Args:
            api: Request and optional pagination configuration.
            context: Variables to render requests and responses with.
            bootstrap: Whether the requests are initializing a session.

        Raises:
            ValueError: If paginated responses are invalid or incomplete.

        Returns:
            Response result, or the combined items when pagination is enabled.
        """
        pagination = api.pagination
        collected, seen, params = [], set(), {}
        for _ in range(pagination.max_pages if pagination else 1):
            response = await self.request(api, context, params, bootstrap=bootstrap)
            body = _body(response)
            response_context = context | {
                "response": {
                    "body": body,
                    "text": response.text,
                    "headers": dict(response.headers),
                    "status": response.status_code,
                }
            }
            default = self.config.response if not bootstrap else None
            for name, check in (("expected", _successful), ("unexpected", _failed)):
                rule = getattr(api.response, name, None)
                if rule is None:
                    rule = getattr(default, name, None)
                valid = check(rule, response.text)
                if valid == (name == "unexpected"):
                    raise KaloscopeException(ErrorCode.HTTP_REQUEST_FAILED)
            if (
                default
                and default.check is not None
                and not _condition(default.check, response_context)
            ):
                raise KaloscopeException(ErrorCode.HTTP_REQUEST_FAILED)
            result = await self.process(api.response, body, response_context)
            if pagination is None:
                return result
            if not isinstance(result, list):
                raise ValueError("RPC pagination must produce a list")
            collected.extend(result)
            token = jsonpath_first(body, pagination.next)
            if not token:
                return collected
            if not isinstance(token, str) or token in seen:
                raise ValueError("RPC pagination repeated an invalid cursor")
            seen.add(token)
            params[pagination.parameter] = token
        raise ValueError("RPC pagination exceeded max_pages")

    async def request(
        self, api: API, context: dict, params: dict, *, bootstrap: bool
    ) -> httpx.Response:
        """Send a request and refresh a rejected session once.

        Args:
            api: The HTTP request configuration.
            context: Shared request variables and current session data.
            params: Additional query parameters for the current page.
            bootstrap: Whether the request is initializing a session.

        Returns:
            The HTTP response before the configured response processing.
        """
        self.requests += 1
        if self.requests > 1024:
            raise ValueError("RPC method exceeded 1024 requests")
        if not bootstrap:
            context["session"] = self.session.data
        generation = self.session.generation

        async def refresh(response: httpx.Response) -> bool:
            """Refresh the session after a configured authentication rejection.

            Args:
                response: Response from the current request attempt.

            Returns:
                Whether the rejected request should be retried.
            """
            if (
                not bootstrap
                and self.config.session
                and response.status_code in self.config.session.refresh_statuses
            ):
                # retry only the rejected request without repeating previous steps
                await self.ensure_session(generation)
                context["session"] = self.session.data
                return True
            return False

        # session-dependent headers are unavailable during authentication
        config = (
            self.config.model_copy(update={"headers": {}}) if bootstrap else self.config
        )
        client = RpcClient(config, self.http)
        result = await client._request(
            api.model_copy(update={"params": (api.params or {}) | params}),
            context,
            api_method=self.method,
            raw_response=True,
            refresh=refresh,
        )
        assert isinstance(result, httpx.Response)
        return result

    async def process(self, spec: APIResponse | None, body: Any, context: dict) -> Any:
        """Validate and transform a response or the result of preceding steps.

        Args:
            spec: Optional response mapping and validation rules.
            body: Response body or result of preceding steps.
            context: Template variables and HTTP response metadata.

        Returns:
            Transformed result, including local file paths when configured.
        """
        if spec is None:
            return body
        context = {"response": {"body": body}} | context
        if spec.check is not None and not _condition(spec.check, context):
            raise KaloscopeException(ErrorCode.HTTP_REQUEST_FAILED)

        def transform(item):
            """Render or map one item from the RPC response.

            Args:
                item: Response item to transform.

            Returns:
                Rendered, mapped or unchanged response item.
            """
            if "transform" in spec.model_fields_set:
                return render(
                    spec.transform, context | {"item": item}, raw=True, strict=True
                )
            return _mapping(item, spec.mappings) if spec.mappings else item

        result = (
            [transform(item) for item in jsonpath_all(body, spec.each)]
            if spec.each
            else transform(body)
        )
        file_context = context | {"item": body}
        if spec.local_files and _condition(spec.local_files.when, file_context):
            if not isinstance(result, dict):
                raise ValueError("RPC local_files requires an object response")
            options = render(
                spec.local_files.model_dump(exclude={"when"}),
                file_context,
                raw=True,
                strict=True,
            )
            result["files"] = await asyncio.to_thread(local_files, **options)
        return result


def _condition(value: bool | str, context: dict) -> bool:
    """Evaluate a boolean value or template condition.

    Args:
        value: Condition to evaluate.
        context: Variables to render the condition with.

    Returns:
        Boolean result of the condition.
    """
    value = render(value, context, raw=True, strict=True)
    if not isinstance(value, bool):
        raise ValueError("RPC conditions must evaluate to a boolean")
    return value


def _body(response: httpx.Response) -> Any:
    """Read a response as JSON, falling back to text.

    Args:
        response: The HTTP response.

    Returns:
        Parsed JSON value or response text.
    """
    try:
        return loads(response.content)
    except ValueError:
        return response.text


def local_files(path: str, exclude: list[str]) -> list[str]:
    """List downloaded files, excluding symlinks.

    Args:
        path: Root file or directory.
        exclude: Glob patterns to skip.

    Raises:
        ValueError: Invalid root, incomplete or empty scan, or over 100000 files.

    Returns:
        Sorted absolute paths with parent aliases preserved.
    """
    if not path or (root := Path(path).absolute()).is_symlink() or not root.exists():
        raise ValueError("RPC file root must be an existing non-symlink path")

    def scan_error(error: OSError):
        """Reject an incomplete directory scan.

        Args:
            error: Filesystem error reported by directory traversal.

        Raises:
            ValueError: If the result directory cannot be fully scanned.
        """
        raise ValueError("RPC file root cannot be fully scanned") from error

    boundary = root.resolve()
    candidates = [root]
    if root.is_dir():
        candidates = (
            directory / name
            for directory, _, names in root.walk(on_error=scan_error)
            for name in names
        )
    else:
        boundary = boundary.parent
    files = []
    for item in candidates:
        if (
            item.is_file()
            and not item.is_symlink()
            and item.resolve().is_relative_to(boundary)
            and not any(item.match(pattern) for pattern in exclude)
        ):
            files.append(str(item))
            if len(files) > 100_000:
                break
    if not 0 < len(files) <= 100_000:
        raise ValueError("RPC file list must contain 1 to 100000 entries")
    return sorted(files)
