"""Diagnostics support for Techem."""

from __future__ import annotations

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry

from .const import DOMAIN
from .data import TechemConfigEntry

TO_REDACT = [CONF_USERNAME, CONF_PASSWORD]


async def async_get_config_entry_diagnostics(
    _hass: HomeAssistant,
    config_entry: TechemConfigEntry,
) -> dict:
    """Return diagnostics for a config entry."""

    coordinator = config_entry.runtime_data.coordinator
    return {
        "config_entry": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "snapshot": coordinator.data.as_dict(),
        "last_update_success": coordinator.last_update_success,
        "last_update_success_time": (
            coordinator.last_update_success_time.isoformat()
            if coordinator.last_update_success_time
            else None
        ),
        "raw_meter_count": len(coordinator.data.raw_devices),
    }


async def async_get_device_diagnostics(
    _hass: HomeAssistant,
    config_entry: ConfigEntry,
    device: DeviceEntry,
) -> dict:
    """Return diagnostics for a specific Techem meter device."""

    device_key = next(
        (identifier for domain, identifier in device.identifiers if domain == DOMAIN),
        None,
    )
    device_id = device_key.split(":", maxsplit=1)[1] if device_key else None
    meter = config_entry.runtime_data.coordinator.data.meters.get(device_id)

    return {
        "config_entry": async_redact_data(config_entry.as_dict(), TO_REDACT),
        "device_id": device_id,
        "meter": meter.as_dict() if meter else None,
    }
