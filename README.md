# Techem for Home Assistant

<p align="center">
  <img src="custom_components/techem/brand/logo.png" alt="Techem" width="420">
</p>

A Home Assistant custom integration for reading Techem meter data from the
Austrian customer portal at `https://kundenportal.techem.at`.

## Why use it

- Native Home Assistant integration with UI setup
- Automatic updates through Home Assistant
- One sensor per active Techem meter
- Built for HACS and ongoing community development

## Requirements

- Home Assistant `2026.3.0` or newer
- A Techem account for `https://kundenportal.techem.at`
- Your portal `username`, `password`, and `unit_id`

## Install

### HACS

1. Open HACS.
2. Add `https://github.com/NewFolk/HA-Techem_at` as a custom repository.
3. Select category `Integration`.
4. Install `Techem`.
5. Restart Home Assistant.

### Manual

1. Copy `custom_components/techem` into your Home Assistant `custom_components`
   directory.
2. Restart Home Assistant.

## Set up

1. Open `Settings -> Devices & Services`.
2. Select `Add Integration`.
3. Search for `Techem`.
4. Enter your `username`, `password`, and `unit_id`.

The integration will create sensors automatically and refresh them on its own
schedule.

## Documentation

| Document | Purpose |
| --- | --- |
| [Technical documentation](docs/TECHNICAL.md) | Architecture, services, development, testing, and release workflow |
| [Changelog](CHANGELOG.md) | Version history starting with `0.1.0` |
| [GitHub Releases](https://github.com/NewFolk/HA-Techem_at/releases) | Published versions for installation and change tracking |

## Notes

- This project currently targets the Austrian Techem portal:
  `https://kundenportal.techem.at`
- `techem.refresh` is available as an optional manual refresh service
- This is an independent community project and is not an official Techem product
