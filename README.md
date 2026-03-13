# Techem for Home Assistant

A native Home Assistant custom integration for Techem meter readings.

Repository: `https://github.com/NewFolk/HA-Techem_at`

## What this repository contains

- UI-based config flow for `username`, `password`, and `unit_id`
- `DataUpdateCoordinator`-driven polling with a default 24 hour interval
- `sensor` entities for every active Techem meter
- optional `techem.refresh` service for manual refreshes and debugging
- diagnostics, reauth, reconfigure, tests, and HACS metadata
- local brand assets in `custom_components/techem/brand/`

## Local beta workflow in this HA config repository

This project currently lives as a local standalone repository at [repos/ha-techem](/root/homeassistant/repos/ha-techem) while it is being developed and validated inside this Home Assistant environment.

Recommended local wiring:

1. Keep the source of truth in `repos/ha-techem`.
2. Expose the live integration through the symlink [custom_components/techem](/root/homeassistant/custom_components/techem).
3. Make that symlink relative, for example `../repos/ha-techem/custom_components/techem`, so it resolves both on the host and inside the Home Assistant container as `/config/...`.
4. Do not point the symlink at a host-only absolute path such as `/root/homeassistant/...`, because the container cannot see that path and the integration will silently disappear from `Add Integration`.
5. Edit code inside `repos/ha-techem`, reload Home Assistant, and test on the live system.
6. When ready, publish `repos/ha-techem` to its own GitHub repository.

## Runtime behavior

- The new integration updates itself on its own schedule through Home Assistant.
- `techem.refresh` is optional and exists only for manual beta checks or debugging.
- The legacy `pyscript` importer and its automation can stay untouched while the new integration is being validated.

## Publishing notes

- GitHub repository: `https://github.com/NewFolk/HA-Techem_at`
- `manifest.json` points users to that repository for documentation and issues.
- Home Assistant and HACS can use `custom_components/techem/brand/icon.png` and `custom_components/techem/brand/logo.png` as local brand assets.

## Development

```bash
cd /config/repos/ha-techem
python3 -m pip install -r requirements_test.txt
pytest
ruff check custom_components tests
```
