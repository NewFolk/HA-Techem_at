"""Sensor platform for Techem."""

from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify

from .const import CONF_UNIT_ID, DOMAIN
from .data import TechemConfigEntry
from .models import TechemMeter


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TechemConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Techem sensors from a config entry."""

    coordinator = entry.runtime_data.coordinator
    known_device_ids: set[str] = set()

    @callback
    def async_add_missing_entities() -> None:
        new_entities = []
        for device_id in coordinator.data.meters:
            if device_id in known_device_ids:
                continue
            known_device_ids.add(device_id)
            new_entities.append(TechemMeterSensor(entry, device_id))

        if new_entities:
            async_add_entities(new_entities)

    async_add_missing_entities()
    entry.async_on_unload(coordinator.async_add_listener(async_add_missing_entities))


class TechemMeterSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Techem meter reading sensor."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:gauge"

    def __init__(self, entry: TechemConfigEntry, device_id: str) -> None:
        """Initialize the sensor."""

        super().__init__(entry.runtime_data.coordinator)
        self._entry = entry
        self._device_id = device_id
        self._attr_unique_id = f"{entry.data[CONF_UNIT_ID]}:{device_id}"

        meter = self.meter
        if meter is not None:
            self._attr_name = meter.entity_name
            self.entity_id = f"sensor.{slugify(meter.suggested_object_id)}"
        else:
            self._attr_name = f"Techem {device_id} Reading"
            self.entity_id = f"sensor.techem_{device_id.lower()}_reading"

    @property
    def meter(self) -> TechemMeter | None:
        """Return the current meter data."""

        return self.coordinator.data.meters.get(self._device_id)

    @property
    def available(self) -> bool:
        """Return whether the entity is available."""

        return super().available and self.meter is not None

    @property
    def device_info(self) -> DeviceInfo:
        """Return the Home Assistant device metadata."""

        meter = self.meter
        identifier = (DOMAIN, f"{self._entry.data[CONF_UNIT_ID]}:{self._device_id}")
        if meter is None:
            return DeviceInfo(identifiers={identifier}, serial_number=self._device_id)

        return DeviceInfo(
            identifiers={identifier},
            manufacturer="Techem",
            name=meter.device_name,
            model=meter.model_name,
            serial_number=self._device_id,
            suggested_area=meter.room_name if meter.room_name != "Unknown" else None,
        )

    @property
    def native_value(self):
        """Return the current sensor value."""

        meter = self.meter
        return meter.reading if meter else None

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the native unit of measurement."""

        meter = self.meter
        return meter.measurement_unit if meter else None

    @property
    def extra_state_attributes(self):
        """Return meter metadata as attributes."""

        meter = self.meter
        return meter.extra_state_attributes if meter else None
