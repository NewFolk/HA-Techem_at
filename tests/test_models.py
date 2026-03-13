"""Tests for Techem payload parsing."""

from __future__ import annotations

import json
from pathlib import Path

from custom_components.techem.models import parse_techem_snapshot

FIXTURE_PATH = Path(__file__).parent / 'fixtures' / 'devices_sample.json'
UNIT_ID = '99990000123456'


def test_parse_snapshot_from_saved_fixture() -> None:
    payload = json.loads(FIXTURE_PATH.read_text(encoding='utf-8'))

    snapshot = parse_techem_snapshot(UNIT_ID, payload)

    assert snapshot.unit_id == UNIT_ID
    assert len(snapshot.meters) == 3
    meter = snapshot.meters['10000000001TST01']
    assert meter.room_slug == 'toilet'
    assert meter.measurement_unit is not None
    assert meter.reading is not None
    assert meter.reading_date is not None


def test_legacy_like_object_id_format() -> None:
    payload = [
        {
            'location': 'modules.rooms.livingRoom',
            'messgeraetenummer2': '10000000004TST01',
            'lastReading': {
                'readingDate': 1730000000000,
                'reading': 12,
                'readingManner': 'auto',
                'readingType': 'monthly',
                'instanceCode': None,
                'reset': False,
            },
            'listOfMeters': [
                {
                    'messgeraetenummer2': '10000000004TST01',
                    'measurementUnit': 'Einh',
                    'aktiv': True,
                    'deviceCategory': 'HEAT_COST_ALLOCATOR',
                    'deviceSubCategory': 'HEAT_COST_ALLOCATOR',
                    'type': 'heat',
                    'calibrationYear': 2025,
                    'installationDate': '2025-01-01',
                    'uninstallationDate': None,
                }
            ],
        }
    ]

    snapshot = parse_techem_snapshot(UNIT_ID, payload)

    meter = snapshot.meters['10000000004TST01']
    assert meter.room_slug == 'livingroom'
    assert (
        meter.suggested_object_id
        == 'techem_10000000004tst01_heat_cost_allocator_livingroom_reading'
    )


def test_parse_snapshot_skips_inactive_meters() -> None:
    payload = [
        {
            'location': 'modules.rooms.kitchen',
            'lastReading': {'reading': '11', 'readingDate': 1730000000000},
            'listOfMeters': [
                {
                    'messgeraetenummer2': 'inactive-1',
                    'measurementUnit': 'kWh',
                    'aktiv': False,
                    'deviceCategory': 'heatMeter',
                    'deviceSubCategory': 'testSubCategory',
                    'type': 'heat',
                    'calibrationYear': 2025,
                    'installationDate': '2025-01-01',
                    'uninstallationDate': None,
                }
            ],
        }
    ]

    snapshot = parse_techem_snapshot(UNIT_ID, payload)

    assert snapshot.meters == {}
