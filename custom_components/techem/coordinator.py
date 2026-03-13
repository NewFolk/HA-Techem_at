"""DataUpdateCoordinator for Techem."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import CONF_UPDATE_INTERVAL_HOURS, DEFAULT_UPDATE_INTERVAL_HOURS, DOMAIN
from .data import TechemConfigEntry
from .exceptions import TechemApiError, TechemAuthError


class TechemDataUpdateCoordinator(DataUpdateCoordinator):
    """Coordinate Techem data updates."""

    config_entry: TechemConfigEntry

    def __init__(self, hass, config_entry: TechemConfigEntry, logger) -> None:
        """Initialize the coordinator."""

        super().__init__(
            hass,
            logger,
            name=f"{DOMAIN}.{config_entry.entry_id}",
            update_interval=timedelta(
                hours=config_entry.options.get(
                    CONF_UPDATE_INTERVAL_HOURS,
                    DEFAULT_UPDATE_INTERVAL_HOURS,
                )
            ),
            config_entry=config_entry,
        )
        self.config_entry = config_entry

    async def _async_update_data(self):
        """Fetch the latest Techem data."""

        try:
            return await self.config_entry.runtime_data.client.async_fetch_snapshot()
        except TechemAuthError as err:
            raise ConfigEntryAuthFailed(err) from err
        except TechemApiError as err:
            raise UpdateFailed(str(err)) from err
