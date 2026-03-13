"""Constants for the Techem integration."""

from __future__ import annotations

from homeassistant.const import Platform

DOMAIN = "techem"
PLATFORMS: list[Platform] = [Platform.SENSOR]

CONF_UNIT_ID = "unit_id"
CONF_UPDATE_INTERVAL_HOURS = "update_interval_hours"

ATTR_ENTRY_ID = "entry_id"
SERVICE_REFRESH = "refresh"

DEFAULT_UPDATE_INTERVAL_HOURS = 24
MIN_UPDATE_INTERVAL_HOURS = 1
MAX_UPDATE_INTERVAL_HOURS = 168

REQUEST_TIMEOUT_SECONDS = 30

PORTAL_BASE_URL = "https://kundenportal.techem.at"
DEFAULT_PORTAL_LANGUAGE = "en"

ENTRY_TITLE_PREFIX = "Techem"
