"""Setup and service tests for Techem."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.techem.const import (
    CONF_UPDATE_INTERVAL_HOURS,
    DEFAULT_UPDATE_INTERVAL_HOURS,
    DOMAIN,
    SERVICE_REFRESH,
)
from custom_components.techem.models import parse_techem_snapshot

USER_INPUT = {
    'username': 'test@example.com',
    'password': 'secret',
    'unit_id': '99990000123456',
}

RAW_PAYLOAD = [
    {
        'location': 'modules.rooms.kitchen',
        'messgeraetenummer2': '10000000003TST01',
        'lastReading': {
            'readingDate': 1730000000000,
            'reading': 15,
            'readingManner': 'auto',
            'readingType': 'monthly',
            'instanceCode': 'instance',
            'reset': False,
        },
        'listOfMeters': [
            {
                'messgeraetenummer2': '10000000003TST01',
                'measurementUnit': 'kWh',
                'aktiv': True,
                'deviceCategory': 'heatMeter',
                'deviceSubCategory': 'roomMeter',
                'type': 'heat',
                'calibrationYear': 2025,
                'installationDate': '2025-01-01',
                'uninstallationDate': None,
            }
        ],
    }
]


class _FakeClientSession:
    """Minimal aiohttp client session stub for setup tests."""

    async def close(self) -> None:
        """Match aiohttp ClientSession.close()."""


async def test_setup_entry_registers_refresh_service(hass) -> None:
    snapshot = parse_techem_snapshot(USER_INPUT['unit_id'], RAW_PAYLOAD)
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
        options={CONF_UPDATE_INTERVAL_HOURS: DEFAULT_UPDATE_INTERVAL_HOURS},
    )
    entry.add_to_hass(hass)

    with (
        patch(
            'custom_components.techem.aiohttp.ClientSession',
            return_value=_FakeClientSession(),
        ),
        patch(
            'custom_components.techem.api.TechemClient.async_fetch_snapshot',
            AsyncMock(return_value=snapshot),
        ) as fetch_snapshot,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        assert fetch_snapshot.await_count == 1
        await hass.services.async_call(DOMAIN, SERVICE_REFRESH, blocking=True)
        await hass.async_block_till_done()
        assert fetch_snapshot.await_count == 2

        await hass.config_entries.async_unload(entry.entry_id)
        await hass.async_block_till_done()
