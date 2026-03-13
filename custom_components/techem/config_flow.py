"""Config flow for the Techem integration."""

from __future__ import annotations

import logging
from typing import Any

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlowWithReload
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .api import DEFAULT_HEADERS, TechemClient
from .const import (
    CONF_UNIT_ID,
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    ENTRY_TITLE_PREFIX,
    MAX_UPDATE_INTERVAL_HOURS,
    MIN_UPDATE_INTERVAL_HOURS,
    REQUEST_TIMEOUT_SECONDS,
)
from .exceptions import TechemApiError, TechemAuthError

LOGGER = logging.getLogger(__name__)


def format_entry_title(unit_id: str) -> str:
    """Return a stable title for a Techem config entry."""

    return f"{ENTRY_TITLE_PREFIX} {unit_id}"


def build_user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    """Build the user-facing schema for config and reconfigure steps."""

    defaults = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_USERNAME, default=defaults.get(CONF_USERNAME, "")): str,
            vol.Required(CONF_PASSWORD, default=defaults.get(CONF_PASSWORD, "")): str,
            vol.Required(CONF_UNIT_ID, default=defaults.get(CONF_UNIT_ID, "")): str,
        }
    )


async def validate_input(_hass, data: dict[str, Any]) -> dict[str, Any]:
    """Validate user input by logging in and fetching the current meter list."""

    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
        cookie_jar=aiohttp.CookieJar(unsafe=True),
        headers=DEFAULT_HEADERS,
    )
    client = TechemClient(
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        unit_id=data[CONF_UNIT_ID],
        session=session,
    )
    try:
        snapshot = await client.async_validate_credentials()
    finally:
        await client.async_close()

    return {
        "title": format_entry_title(data[CONF_UNIT_ID]),
        "meter_count": len(snapshot.meters),
    }


class TechemConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Techem."""

    _entry: ConfigEntry | None = None

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle the initial config flow step."""

        errors: dict[str, str] = {}

        if user_input is not None:
            data = {
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_UNIT_ID: user_input[CONF_UNIT_ID].strip(),
            }
            try:
                info = await validate_input(self.hass, data)
            except TechemAuthError:
                errors["base"] = "invalid_auth"
            except TechemApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-exception-caught
                LOGGER.exception("Unexpected exception during Techem config flow")
                errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(data[CONF_UNIT_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=info["title"], data=data)

        return self.async_show_form(
            step_id="user",
            data_schema=build_user_schema(user_input),
            errors=errors,
        )

    async def async_step_reauth(
        self,
        _user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Start re-authentication flow."""

        entry_id = self.context.get("entry_id")
        self._entry = self.hass.config_entries.async_get_entry(entry_id)
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle re-authentication."""

        if self._entry is None:
            return self.async_abort(reason="entry_not_found")

        errors: dict[str, str] = {}
        if user_input is not None:
            data = {
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_UNIT_ID: self._entry.data[CONF_UNIT_ID],
            }
            try:
                await validate_input(self.hass, data)
            except TechemAuthError:
                errors["base"] = "invalid_auth"
            except TechemApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-exception-caught
                LOGGER.exception("Unexpected exception during Techem reauth")
                errors["base"] = "unknown"
            else:
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    data={
                        **self._entry.data,
                        CONF_USERNAME: data[CONF_USERNAME],
                        CONF_PASSWORD: data[CONF_PASSWORD],
                    },
                )
                await self.hass.config_entries.async_reload(self._entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_USERNAME,
                        default=self._entry.data[CONF_USERNAME],
                    ): str,
                    vol.Required(CONF_PASSWORD): str,
                }
            ),
            errors=errors,
        )

    async def async_step_reconfigure(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Handle reconfiguration of credentials or unit ID."""

        entry_id = self.context.get("entry_id")
        self._entry = self.hass.config_entries.async_get_entry(entry_id)
        if self._entry is None:
            return self.async_abort(reason="entry_not_found")

        errors: dict[str, str] = {}
        defaults = {
            CONF_USERNAME: self._entry.data[CONF_USERNAME],
            CONF_UNIT_ID: self._entry.data[CONF_UNIT_ID],
        }

        if user_input is not None:
            data = {
                CONF_USERNAME: user_input[CONF_USERNAME].strip(),
                CONF_PASSWORD: user_input[CONF_PASSWORD],
                CONF_UNIT_ID: user_input[CONF_UNIT_ID].strip(),
            }
            try:
                await validate_input(self.hass, data)
            except TechemAuthError:
                errors["base"] = "invalid_auth"
            except TechemApiError:
                errors["base"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-exception-caught
                LOGGER.exception("Unexpected exception during Techem reconfigure")
                errors["base"] = "unknown"
            else:
                duplicate = next(
                    (
                        entry
                        for entry in self._async_current_entries()
                        if entry.entry_id != self._entry.entry_id
                        and entry.unique_id == data[CONF_UNIT_ID]
                    ),
                    None,
                )
                if duplicate is not None:
                    errors["base"] = "already_configured"
                else:
                    self.hass.config_entries.async_update_entry(
                        self._entry,
                        data=data,
                        title=format_entry_title(data[CONF_UNIT_ID]),
                        unique_id=data[CONF_UNIT_ID],
                    )
                    await self.hass.config_entries.async_reload(self._entry.entry_id)
                    return self.async_abort(reason="reconfigure_successful")

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=build_user_schema(defaults),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlowWithReload:
        """Return the options flow handler."""

        return TechemOptionsFlowHandler()


class TechemOptionsFlowHandler(OptionsFlowWithReload):
    """Handle Techem options."""

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> FlowResult:
        """Manage the options step."""

        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL_HOURS,
                        default=self.config_entry.options.get(
                            CONF_UPDATE_INTERVAL_HOURS,
                            DEFAULT_UPDATE_INTERVAL_HOURS,
                        ),
                    ): vol.All(
                        int,
                        vol.Range(
                            min=MIN_UPDATE_INTERVAL_HOURS,
                            max=MAX_UPDATE_INTERVAL_HOURS,
                        ),
                    ),
                }
            ),
        )
