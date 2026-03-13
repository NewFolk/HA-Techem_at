"""The Techem integration."""

from __future__ import annotations

import asyncio
import logging

import aiohttp
import voluptuous as vol
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import ServiceValidationError

from .api import DEFAULT_HEADERS, TechemClient
from .const import (
    ATTR_ENTRY_ID,
    CONF_UNIT_ID,
    DOMAIN,
    PLATFORMS,
    REQUEST_TIMEOUT_SECONDS,
    SERVICE_REFRESH,
)
from .coordinator import TechemDataUpdateCoordinator
from .data import TechemConfigEntry, TechemRuntimeData

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, _config: dict) -> bool:
    """Set up the Techem integration domain."""

    hass.data.setdefault(DOMAIN, {"services_registered": False})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: TechemConfigEntry) -> bool:
    """Set up Techem from a config entry."""

    domain_data = hass.data.setdefault(DOMAIN, {"services_registered": False})
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT_SECONDS),
        cookie_jar=aiohttp.CookieJar(unsafe=True),
        headers=DEFAULT_HEADERS,
    )
    client = TechemClient(
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        unit_id=entry.data[CONF_UNIT_ID],
        session=session,
    )
    coordinator = TechemDataUpdateCoordinator(hass, entry, LOGGER)
    entry.runtime_data = TechemRuntimeData(client=client, coordinator=coordinator)

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        await client.async_close()
        raise

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    if not domain_data.get("services_registered"):
        _async_setup_services(hass)
        domain_data["services_registered"] = True

    return True


async def async_unload_entry(hass: HomeAssistant, entry: TechemConfigEntry) -> bool:
    """Unload a config entry."""

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    await entry.runtime_data.client.async_close()

    remaining_loaded = any(
        config_entry.entry_id != entry.entry_id
        and config_entry.state is ConfigEntryState.LOADED
        for config_entry in hass.config_entries.async_entries(DOMAIN)
    )
    if not remaining_loaded and hass.services.has_service(DOMAIN, SERVICE_REFRESH):
        hass.services.async_remove(DOMAIN, SERVICE_REFRESH)
        hass.data.setdefault(DOMAIN, {})["services_registered"] = False

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: TechemConfigEntry) -> None:
    """Reload Techem after options or reconfigure changes."""

    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    _hass: HomeAssistant,
    _entry: TechemConfigEntry,
    _device,
) -> bool:
    """Allow removing devices from the entry."""

    return True


def _async_setup_services(hass: HomeAssistant) -> None:
    """Register Techem services."""

    schema = vol.Schema({vol.Optional(ATTR_ENTRY_ID): str})

    async def async_handle_refresh(call: ServiceCall) -> None:
        entry_id = call.data.get(ATTR_ENTRY_ID)
        if entry_id:
            target_entry = hass.config_entries.async_get_entry(entry_id)
            if target_entry is None or target_entry.domain != DOMAIN:
                raise ServiceValidationError(
                    f"Unknown Techem config entry: {entry_id}"
                )
            if target_entry.state is not ConfigEntryState.LOADED:
                raise ServiceValidationError(
                    f"Techem config entry is not loaded: {entry_id}"
                )
            entries = [target_entry]
        else:
            entries = [
                entry
                for entry in hass.config_entries.async_entries(DOMAIN)
                if entry.state is ConfigEntryState.LOADED
            ]

        if not entries:
            raise ServiceValidationError("No loaded Techem config entries found")

        await asyncio.gather(
            *(
                entry.runtime_data.coordinator.async_request_refresh()
                for entry in entries
            )
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_REFRESH,
        async_handle_refresh,
        schema=schema,
    )
