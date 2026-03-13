"""Data models and parsers for Techem meter data."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from .exceptions import TechemParseError

ROOM_MAPPING: dict[str, str] = {
    "modules.rooms.kitchen": "kitchen",
    "modules.rooms.bath": "bath",
    "modules.rooms.room": "room",
    "modules.rooms.toilet": "toilet",
    "modules.rooms.livingRoom": "livingroom",
}

ROOM_DISPLAY_MAPPING: dict[str, str] = {
    "kitchen": "Kitchen",
    "bath": "Bath",
    "room": "Room",
    "toilet": "Toilet",
    "livingroom": "Living Room",
}


def humanize_identifier(value: str | None, *, fallback: str) -> str:
    """Convert camelCase or snake_case values into a readable label."""

    if not value:
        return fallback

    normalized = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
    normalized = normalized.replace("_", " ").replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized.title() if normalized else fallback


def normalize_room(location: str | None) -> tuple[str, str]:
    """Normalize Techem room keys into a stable slug and display label."""

    if location in ROOM_MAPPING:
        room_slug = ROOM_MAPPING[location]
    elif location:
        room_slug = location.rsplit(".", maxsplit=1)[-1].replace(" ", "_").lower()
    else:
        room_slug = "unknown"

    return room_slug, ROOM_DISPLAY_MAPPING.get(
        room_slug,
        humanize_identifier(room_slug, fallback="Unknown"),
    )


def normalize_reading(value: Any) -> int | float | str | None:
    """Normalize readings into HA-friendly scalar values."""

    if value is None:
        return None

    if isinstance(value, bool):
        return int(value)

    if isinstance(value, int | float):
        return value

    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        try:
            if "." not in stripped and "," not in stripped:
                return int(stripped)
            return float(stripped.replace(",", "."))
        except ValueError:
            return stripped

    return str(value)


def parse_reading_date(value: Any) -> datetime | None:
    """Convert Techem millisecond timestamps into UTC datetimes."""

    if value in (None, ""):
        return None

    try:
        timestamp_ms = int(value)
    except (TypeError, ValueError):
        return None

    return datetime.fromtimestamp(timestamp_ms / 1000, UTC)


@dataclass(slots=True)
class TechemMeter:
    """Normalized representation of a Techem meter."""

    unit_id: str
    device_id: str
    room_key: str | None
    room_slug: str
    room_name: str
    category: str | None
    category_name: str
    subcategory: str | None
    measurement_unit: str | None
    reading: int | float | str | None
    reading_date: datetime | None
    reading_type: str | None
    reading_manner: str | None
    instance_code: str | None
    reset: bool | None
    calibration_year: str | int | None
    meter_type: str | None
    installation_date: str | None
    uninstallation_date: str | None
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    @property
    def category_slug(self) -> str:
        """Return a stable slug for the meter category."""

        if self.category:
            return self.category.lower()
        return "meter"

    @property
    def device_name(self) -> str:
        """Return a friendly device name."""

        if self.room_name == "Unknown":
            return f"Techem {self.device_id} {self.category_name}"
        return f"Techem {self.device_id} {self.category_name} {self.room_name}"

    @property
    def entity_name(self) -> str:
        """Return the sensor friendly name."""

        if self.room_name == "Unknown":
            return f"Techem {self.device_id} {self.category_name} Reading"
        return f"Techem {self.device_id} {self.category_name} {self.room_name} Reading"

    @property
    def suggested_object_id(self) -> str:
        """Return a stable entity object id close to the legacy naming."""

        return (
            f"techem_{self.device_id.lower()}_"
            f"{self.category_slug}_{self.room_slug}_reading"
        )

    @property
    def model_name(self) -> str:
        """Return a friendly device model."""

        if self.subcategory:
            subcategory = humanize_identifier(
                self.subcategory,
                fallback=self.subcategory,
            )
            return f"{self.category_name} / {subcategory}"
        return self.category_name

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return HA sensor attributes for a meter."""

        return {
            "unit_id": self.unit_id,
            "meter_id": self.device_id,
            "room": self.room_name,
            "room_slug": self.room_slug,
            "device_category": self.category_name,
            "device_subcategory": self.subcategory,
            "measurement_unit": self.measurement_unit,
            "reading_date": (
                self.reading_date.isoformat() if self.reading_date else None
            ),
            "reading_type": self.reading_type,
            "reading_manner": self.reading_manner,
            "instance_code": self.instance_code,
            "reset": self.reset,
            "calibration_year": self.calibration_year,
            "meter_type": self.meter_type,
            "installation_date": self.installation_date,
            "uninstallation_date": self.uninstallation_date,
        }

    def as_dict(self) -> dict[str, Any]:
        """Serialize the meter for diagnostics."""

        return {
            "device_id": self.device_id,
            "room_key": self.room_key,
            "room_slug": self.room_slug,
            "room_name": self.room_name,
            "category": self.category,
            "category_name": self.category_name,
            "subcategory": self.subcategory,
            "measurement_unit": self.measurement_unit,
            "reading": self.reading,
            "reading_date": (
                self.reading_date.isoformat() if self.reading_date else None
            ),
            "reading_type": self.reading_type,
            "reading_manner": self.reading_manner,
            "instance_code": self.instance_code,
            "reset": self.reset,
            "calibration_year": self.calibration_year,
            "meter_type": self.meter_type,
            "installation_date": self.installation_date,
            "uninstallation_date": self.uninstallation_date,
        }


@dataclass(slots=True)
class TechemSnapshot:
    """Snapshot of the current Techem meter data."""

    unit_id: str
    fetched_at: datetime
    meters: dict[str, TechemMeter]
    raw_devices: list[dict[str, Any]] = field(repr=False, default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        """Serialize the snapshot for diagnostics."""

        return {
            "unit_id": self.unit_id,
            "fetched_at": self.fetched_at.isoformat(),
            "meter_count": len(self.meters),
            "meters": {
                device_id: meter.as_dict() for device_id, meter in self.meters.items()
            },
        }


def parse_techem_snapshot(
    unit_id: str,
    payload: Any,
    *,
    fetched_at: datetime | None = None,
) -> TechemSnapshot:
    """Parse raw Techem payload into a snapshot."""

    if not isinstance(payload, list):
        raise TechemParseError("Expected Techem payload to be a list of devices")

    meters: dict[str, TechemMeter] = {}
    raw_devices: list[dict[str, Any]] = []

    for item in payload:
        if not isinstance(item, dict):
            continue

        raw_devices.append(item)
        list_of_meters = item.get("listOfMeters")
        if isinstance(list_of_meters, list) and list_of_meters:
            meter_info = list_of_meters[0]
        else:
            meter_info = {}
        if not isinstance(meter_info, dict):
            continue

        if not meter_info.get("aktiv", False):
            continue

        device_id = str(
            meter_info.get("messgeraetenummer2")
            or item.get("messgeraetenummer2")
            or ""
        ).strip()
        if not device_id:
            continue

        last_reading = item.get("lastReading")
        if not isinstance(last_reading, dict):
            last_reading = {}

        room_slug, room_name = normalize_room(item.get("location"))
        category = meter_info.get("deviceCategory")

        meters[device_id] = TechemMeter(
            unit_id=unit_id,
            device_id=device_id,
            room_key=item.get("location"),
            room_slug=room_slug,
            room_name=room_name,
            category=category,
            category_name=humanize_identifier(category, fallback="Meter"),
            subcategory=meter_info.get("deviceSubCategory"),
            measurement_unit=meter_info.get("measurementUnit"),
            reading=normalize_reading(last_reading.get("reading")),
            reading_date=parse_reading_date(last_reading.get("readingDate")),
            reading_type=last_reading.get("readingType"),
            reading_manner=last_reading.get("readingManner"),
            instance_code=last_reading.get("instanceCode"),
            reset=last_reading.get("reset"),
            calibration_year=meter_info.get("calibrationYear"),
            meter_type=meter_info.get("type"),
            installation_date=meter_info.get("installationDate"),
            uninstallation_date=meter_info.get("uninstallationDate"),
            raw=item,
        )

    return TechemSnapshot(
        unit_id=unit_id,
        fetched_at=fetched_at or datetime.now(UTC),
        meters=meters,
        raw_devices=raw_devices,
    )
