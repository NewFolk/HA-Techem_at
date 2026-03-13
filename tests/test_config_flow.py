"""Config flow tests for Techem."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.techem.const import DOMAIN

USER_INPUT = {
    'username': 'test@example.com',
    'password': 'secret',
    'unit_id': '99990000123456',
}


async def test_user_flow_creates_entry(hass) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={'source': 'user'},
    )

    with patch(
        'custom_components.techem.config_flow.validate_input',
        AsyncMock(return_value={'title': 'Techem 99990000123456', 'meter_count': 3}),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            USER_INPUT,
        )

    assert result2['type'] is FlowResultType.CREATE_ENTRY
    assert result2['title'] == 'Techem 99990000123456'
    assert result2['data'] == USER_INPUT


async def test_user_flow_aborts_when_unit_already_configured(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={'source': 'user'},
    )

    with patch(
        'custom_components.techem.config_flow.validate_input',
        AsyncMock(return_value={'title': 'Techem 99990000123456', 'meter_count': 3}),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            USER_INPUT,
        )

    assert result2['type'] is FlowResultType.ABORT
    assert result2['reason'] == 'already_configured'
