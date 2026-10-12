import time
from http.cookiejar import Cookie, CookieJar
from multiprocessing.managers import DictProxy
from multiprocessing.synchronize import RLock

from sanic import Sanic

from app.models.general import GlobalCookie


class SQLiteCookieJar(CookieJar):
    """SQLite-backed cookie jar."""

    def __init__(self, app: Sanic, policy=None):
        """Use the shared cookie store and lock.

        Args:
            app: Application holding the shared cookie state.
            policy: Cookie acceptance policy; `None` uses the standard policy.
        """
        super().__init__(policy)
        self._cookies: DictProxy = app.shared_ctx.cookies
        self._cookies_lock: RLock = app.shared_ctx.cookies_lock

    def set_cookie(self, cookie):
        """Store a cookie without checking the acceptance policy.

        Args:
            cookie: Cookie to store.
        """
        c = self._cookies
        self._cookies_lock.acquire()
        try:
            if cookie.domain not in c:
                c[cookie.domain] = {}
            c2 = c[cookie.domain]
            if cookie.path not in c2:
                c2[cookie.path] = {}
            c3 = c2[cookie.path]
            c3[cookie.name] = cookie
            # update nested dict
            c[cookie.domain] = c2
        finally:
            self._cookies_lock.release()

    def get_cookie(self, domain, path=None, name=None):
        """Find a cookie that has not expired.

        Args:
            domain: Cookie domain.
            path: Cookie path; `None` searches all paths in the domain.
            name: Cookie name; `None` returns the first match.

        Returns:
            Matching cookie, or `None` if no valid cookie exists.
        """
        c2 = self._cookies.get(domain)
        if not c2:
            return None

        now = time.time()

        def not_expired(cookie):
            """Check expiry against the captured lookup time.

            Args:
                cookie: Cookie to check.

            Returns:
                Whether the cookie has no expiry or is still valid.
            """
            return cookie.expires is None or cookie.expires >= now

        if path is not None and path in c2:
            c3 = c2[path]
            if name is not None and name in c3:
                cookie = c3[name]
                if not_expired(cookie):
                    return cookie
            elif name is None:
                for cookie in c3.values():
                    if not_expired(cookie):
                        return cookie
        elif path is None:
            for c3 in c2.values():
                for cookie in c3.values():
                    if not_expired(cookie):
                        return cookie

    def clear(self, domain=None, path=None, name=None):
        """Remove cookies within the selected scope.

        Args:
            domain: Domain to clear; `None` clears all cookies.
            path: Path to clear; `None` clears the whole domain.
            name: Cookie name; `None` clears all cookies in the selected path.

        Raises:
            KeyError: If the selected domain, path or cookie does not exist.
            ValueError: If a path or name lacks its required domain or path scope.
        """
        if name is not None:
            if (domain is None) or (path is None):
                raise ValueError(
                    "domain and path must be given to remove a cookie by name"
                )
            c2 = self._cookies[domain]
            del c2[path][name]
            # update nested dict
            self._cookies[domain] = c2
        elif path is not None:
            if domain is None:
                raise ValueError("domain must be given to remove cookies by path")
            c2 = self._cookies[domain]
            del c2[path]
            # update nested dict
            self._cookies[domain] = c2
        elif domain is not None:
            del self._cookies[domain]
        else:
            self._cookies.clear()

    async def load(self):
        """Load cookies from the database."""
        if self._cookies_lock.acquire(block=False):
            try:
                now = time.time()
                await GlobalCookie.filter(expires__lt=now).delete()
                cookies = await GlobalCookie.filter(expires__gte=now)
                for cookie in cookies:
                    self.set_cookie(
                        Cookie(
                            version=0,
                            name=cookie.name,
                            value=cookie.value,
                            port=None,
                            port_specified=False,
                            domain=cookie.domain,
                            domain_specified=bool(cookie.domain),
                            domain_initial_dot=cookie.domain.startswith("."),
                            path=cookie.path,
                            path_specified=bool(cookie.path),
                            secure=False,
                            expires=cookie.expires,
                            discard=False,
                            comment=None,
                            comment_url=None,
                            rest={},
                            rfc2109=False,
                        )
                    )
            finally:
                self._cookies_lock.release()

    async def save(self):
        """Save cookies to database."""
        if self._cookies_lock.acquire(block=False):
            try:
                now = time.time()
                for cookie in self:
                    if cookie.discard or cookie.expires is None or cookie.expires < now:
                        continue
                    _cookie = await GlobalCookie.get_or_none(
                        name=cookie.name,
                        domain=cookie.domain,
                        path=cookie.path,
                    )
                    if _cookie is not None:
                        await GlobalCookie.filter(id=_cookie.id).update(
                            value=cookie.value,
                            expires=cookie.expires,
                        )
                    else:
                        await GlobalCookie.create(
                            name=cookie.name,
                            value=cookie.value,
                            domain=cookie.domain,
                            path=cookie.path,
                            expires=cookie.expires,
                        )
            finally:
                self._cookies_lock.release()
