"""Runtime types for the Techem integration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry

    from .api import TechemClient
    from .coordinator import TechemDataUpdateCoordinator

type TechemConfigEntry = ConfigEntry[TechemRuntimeData]


@dataclass(slots=True)
class TechemRuntimeData:
    """Runtime data attached to a config entry."""

    client: TechemClient
    coordinator: TechemDataUpdateCoordinator
