"""Async client for the Techem customer portal."""

from __future__ import annotations

import asyncio
import re
from datetime import UTC, datetime
from typing import Any

import aiohttp

from .const import DEFAULT_PORTAL_LANGUAGE, PORTAL_BASE_URL
from .exceptions import TechemApiError, TechemAuthError
from .models import TechemSnapshot, parse_techem_snapshot

DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Safari/605.1.15"
    ),
    "Accept": "text/html,application/xhtml+xml",
}

LOGIN_PATH = (
    "/home"
    "?p_p_id=com_liferay_login_web_portlet_LoginPortlet_INSTANCE_irfelogin"
    "&p_p_lifecycle=1"
    "&p_p_state=normal"
    "&p_p_mode=view"
    "&_com_liferay_login_web_portlet_LoginPortlet_INSTANCE_irfelogin_javax.portlet.action=%2Flogin%2Flogin"
    "&_com_liferay_login_web_portlet_LoginPortlet_INSTANCE_irfelogin_mvcRenderCommandName=%2Flogin%2Flogin"
)
LOGIN_FIELD_PREFIX = "_com_liferay_login_web_portlet_LoginPortlet_INSTANCE_irfelogin_"

P_AUTH_PATTERNS = (
    re.compile(r"p_auth=([A-Za-z0-9_-]+)"),
    re.compile(r"p_auth\\x3[dD]([A-Za-z0-9_-]+)"),
    re.compile(r"p_auth\\u003[dD]([A-Za-z0-9_-]+)"),
)
CSRF_META_PATTERN = re.compile(
    r'<meta[^>]+name=["\']csrf-token["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
CSRF_META_PATTERN_REVERSED = re.compile(
    r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+name=["\']csrf-token["\']',
    re.IGNORECASE,
)
CSRF_SCRIPT_PATTERN = re.compile(r'Liferay\.authToken\s*=\s*["\']([^"\']+)["\']')


def extract_portal_auth_token(html: str) -> str | None:
    """Extract the portal p_auth token from a page."""

    for pattern in P_AUTH_PATTERNS:
        match = pattern.search(html)
        if match:
            return match.group(1)
    return None


def extract_csrf_token(html: str) -> str | None:
    """Extract the Techem CSRF token from a page."""

    for pattern in (CSRF_META_PATTERN, CSRF_META_PATTERN_REVERSED, CSRF_SCRIPT_PATTERN):
        match = pattern.search(html)
        if match:
            return match.group(1)
    return None


def looks_like_login_page(html: str) -> bool:
    """Detect whether the returned HTML is still the login page."""

    return "LoginPortlet" in html or f'{LOGIN_FIELD_PREFIX}login' in html


class TechemClient:
    """Client for Techem's customer portal."""

    def __init__(
        self,
        *,
        username: str,
        password: str,
        unit_id: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """Initialize the client."""

        self._username = username
        self._password = password
        self._unit_id = unit_id
        self._session = session
        self._lock = asyncio.Lock()

    @property
    def username(self) -> str:
        """Return the configured username."""

        return self._username

    @property
    def unit_id(self) -> str:
        """Return the configured unit ID."""

        return self._unit_id

    async def async_close(self) -> None:
        """Close the underlying HTTP session."""

        await self._session.close()

    async def async_validate_credentials(self) -> TechemSnapshot:
        """Validate credentials by performing a full data fetch."""

        return await self.async_fetch_snapshot()

    async def async_fetch_snapshot(self) -> TechemSnapshot:
        """Fetch the latest Techem meter snapshot."""

        async with self._lock:
            self._session.cookie_jar.clear()

            try:
                home_html = await self._async_get_text(f"{PORTAL_BASE_URL}/")
                p_auth = extract_portal_auth_token(home_html)
                if not p_auth:
                    raise TechemApiError("Unable to extract Techem p_auth token")

                await self._async_login(p_auth)
                await self._async_get_text(
                    f"{PORTAL_BASE_URL}/{DEFAULT_PORTAL_LANGUAGE}/home"
                )
                devices_html = await self._async_get_text(
                    f"{PORTAL_BASE_URL}/{DEFAULT_PORTAL_LANGUAGE}/devices"
                )

                csrf_token = extract_csrf_token(devices_html)
                if not csrf_token:
                    if looks_like_login_page(devices_html):
                        raise TechemAuthError("Techem login failed")
                    raise TechemApiError("Unable to extract Techem CSRF token")

                payload = await self._async_get_json(
                    f"{PORTAL_BASE_URL}/o/rest/meter-device/list?unit_id={self._unit_id}",
                    headers={
                        "Accept": "application/json, text/plain, */*",
                        "Referer": (
                            f"{PORTAL_BASE_URL}/{DEFAULT_PORTAL_LANGUAGE}/devices"
                        ),
                        "User-Agent": DEFAULT_HEADERS["User-Agent"],
                        "X-CSRF-TOKEN": csrf_token,
                    },
                )
            except aiohttp.ClientResponseError as err:
                if err.status in (401, 403):
                    raise TechemAuthError(
                        f"Techem authentication failed: {err.status}"
                    ) from err
                raise TechemApiError(
                    f"Techem API request failed: {err.status}"
                ) from err
            except aiohttp.ClientError as err:
                raise TechemApiError(f"Failed to reach Techem: {err}") from err

        return parse_techem_snapshot(
            self._unit_id,
            payload,
            fetched_at=datetime.now(UTC),
        )

    async def _async_login(self, p_auth: str) -> None:
        """Authenticate against the Techem portal."""

        payload = {
            f"{LOGIN_FIELD_PREFIX}formDate": str(
                int(datetime.now(UTC).timestamp() * 1000)
            ),
            f"{LOGIN_FIELD_PREFIX}saveLastPath": "false",
            f"{LOGIN_FIELD_PREFIX}redirect": "",
            f"{LOGIN_FIELD_PREFIX}doActionAfterLogin": "false",
            f"{LOGIN_FIELD_PREFIX}login": self._username,
            f"{LOGIN_FIELD_PREFIX}password": self._password,
            f"{LOGIN_FIELD_PREFIX}rememberMe": "true",
            f"{LOGIN_FIELD_PREFIX}checkboxNames": "rememberMe",
            "p_auth": p_auth,
        }
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": PORTAL_BASE_URL,
            "Referer": f"{PORTAL_BASE_URL}/",
            "User-Agent": DEFAULT_HEADERS["User-Agent"],
            "Accept": DEFAULT_HEADERS["Accept"],
        }

        await self._async_post_text(
            f"{PORTAL_BASE_URL}{LOGIN_PATH}",
            data=payload,
            headers=headers,
        )

    async def _async_get_text(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> str:
        """Fetch a text response."""

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    async def _async_post_text(
        self,
        url: str,
        *,
        data: dict[str, Any],
        headers: dict[str, str] | None = None,
    ) -> str:
        """Send a POST request and return the response text."""

        async with self._session.post(url, data=data, headers=headers) as response:
            response.raise_for_status()
            return await response.text()

    async def _async_get_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
    ) -> Any:
        """Fetch a JSON response."""

        async with self._session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()
