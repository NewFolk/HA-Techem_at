"""Config flow tests for Techem."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.techem.const import DOMAIN
from custom_components.techem.exceptions import TechemAuthError
from custom_components.techem.models import parse_techem_snapshot

USER_INPUT = {
    'username': 'test@example.com',
    'password': 'secret',
    'unit_id': '99990000123456',
}


async def test_user_flow_creates_entry(hass) -> None:
    snapshot = parse_techem_snapshot(USER_INPUT['unit_id'], [])

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={'source': 'user'},
    )

    with (
        patch(
            'custom_components.techem.config_flow.validate_input',
            AsyncMock(
                return_value={'title': 'Techem 99990000123456', 'meter_count': 3}
            ),
        ),
        patch(
            'custom_components.techem.async_setup_entry',
            AsyncMock(return_value=True),
        ),
        patch(
            'custom_components.techem.api.TechemClient.async_fetch_snapshot',
            AsyncMock(return_value=snapshot),
        ),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result2['type'] is FlowResultType.CREATE_ENTRY
    assert result2['title'] == 'Techem 99990000123456'
    assert result2['data'] == USER_INPUT

    entry = hass.config_entries.async_entries(DOMAIN)[0]
    await hass.config_entries.async_remove(entry.entry_id)
    await hass.async_block_till_done()


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


async def test_reauth_flow_updates_credentials_and_reloads_entry(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    updated_credentials = {
        CONF_USERNAME: 'updated@example.com',
        CONF_PASSWORD: 'new-secret',
    }

    with (
        patch(
            'custom_components.techem.config_flow.validate_input',
            AsyncMock(return_value={'title': entry.title, 'meter_count': 3}),
        ),
        patch.object(
            hass.config_entries,
            'async_reload',
            AsyncMock(return_value=True),
        ) as reload_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                'source': SOURCE_REAUTH,
                'entry_id': entry.entry_id,
                'unique_id': entry.unique_id,
                'title_placeholders': {'name': entry.title},
            },
            data=entry.data,
        )

        assert result['type'] is FlowResultType.FORM
        assert result['step_id'] == 'reauth_confirm'

        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            updated_credentials,
        )
        await hass.async_block_till_done()

    assert result2['type'] is FlowResultType.ABORT
    assert result2['reason'] == 'reauth_successful'
    assert entry.data[CONF_USERNAME] == updated_credentials[CONF_USERNAME]
    assert entry.data[CONF_PASSWORD] == updated_credentials[CONF_PASSWORD]
    assert entry.data['unit_id'] == USER_INPUT['unit_id']
    reload_entry.assert_awaited_once_with(entry.entry_id)


async def test_reauth_flow_shows_error_on_invalid_auth(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    with (
        patch(
            'custom_components.techem.config_flow.validate_input',
            AsyncMock(side_effect=TechemAuthError),
        ),
        patch.object(
            hass.config_entries,
            'async_reload',
            AsyncMock(return_value=True),
        ) as reload_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                'source': SOURCE_REAUTH,
                'entry_id': entry.entry_id,
                'unique_id': entry.unique_id,
                'title_placeholders': {'name': entry.title},
            },
            data=entry.data,
        )

        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            {
                CONF_USERNAME: USER_INPUT[CONF_USERNAME],
                CONF_PASSWORD: 'wrong-password',
            },
        )
        await hass.async_block_till_done()

    assert result2['type'] is FlowResultType.FORM
    assert result2['step_id'] == 'reauth_confirm'
    assert result2['errors'] == {'base': 'invalid_auth'}
    assert entry.data == USER_INPUT
    reload_entry.assert_not_awaited()


async def test_reconfigure_flow_updates_entry_identity_and_reloads(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    updated_data = {
        CONF_USERNAME: 'updated@example.com',
        CONF_PASSWORD: 'new-secret',
        'unit_id': '99990000999999',
    }

    with (
        patch(
            'custom_components.techem.config_flow.validate_input',
            AsyncMock(
                return_value={
                    'title': 'Techem 99990000999999',
                    'meter_count': 4,
                }
            ),
        ),
        patch.object(
            hass.config_entries,
            'async_reload',
            AsyncMock(return_value=True),
        ) as reload_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                'source': SOURCE_RECONFIGURE,
                'entry_id': entry.entry_id,
                'unique_id': entry.unique_id,
                'title_placeholders': {'name': entry.title},
            },
        )

        assert result['type'] is FlowResultType.FORM
        assert result['step_id'] == 'reconfigure'

        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            updated_data,
        )
        await hass.async_block_till_done()

    assert result2['type'] is FlowResultType.ABORT
    assert result2['reason'] == 'reconfigure_successful'
    assert entry.data == updated_data
    assert entry.unique_id == updated_data['unit_id']
    assert entry.title == 'Techem 99990000999999'
    reload_entry.assert_awaited_once_with(entry.entry_id)


async def test_reconfigure_flow_blocks_duplicate_unit_id(hass) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=USER_INPUT['unit_id'],
        title='Techem 99990000123456',
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    duplicate_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id='99990000999999',
        title='Techem 99990000999999',
        data={
            CONF_USERNAME: 'other@example.com',
            CONF_PASSWORD: 'other-secret',
            'unit_id': '99990000999999',
        },
    )
    duplicate_entry.add_to_hass(hass)

    attempted_data = {
        CONF_USERNAME: 'updated@example.com',
        CONF_PASSWORD: 'new-secret',
        'unit_id': duplicate_entry.unique_id,
    }

    with (
        patch(
            'custom_components.techem.config_flow.validate_input',
            AsyncMock(
                return_value={
                    'title': 'Techem 99990000999999',
                    'meter_count': 4,
                }
            ),
        ),
        patch.object(
            hass.config_entries,
            'async_reload',
            AsyncMock(return_value=True),
        ) as reload_entry,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={
                'source': SOURCE_RECONFIGURE,
                'entry_id': entry.entry_id,
                'unique_id': entry.unique_id,
                'title_placeholders': {'name': entry.title},
            },
        )

        result2 = await hass.config_entries.flow.async_configure(
            result['flow_id'],
            attempted_data,
        )
        await hass.async_block_till_done()

    assert result2['type'] is FlowResultType.FORM
    assert result2['step_id'] == 'reconfigure'
    assert result2['errors'] == {'base': 'already_configured'}
    assert entry.data == USER_INPUT
    assert entry.unique_id == USER_INPUT['unit_id']
    assert entry.title == 'Techem 99990000123456'
    reload_entry.assert_not_awaited()
