# Technical Documentation

## Scope

This integration currently supports the Austrian Techem customer portal:

- `https://kundenportal.techem.at`

## Compatibility

- Home Assistant `2026.3.0` or newer
- Current integration version: `0.1.0`

## Technical overview

- UI config flow with:
  - `username`
  - `password`
  - `unit_id`
- `DataUpdateCoordinator`-based polling
- One sensor entity per active meter
- Reauth and reconfigure flows
- Diagnostics support
- Optional manual refresh service:
  - `techem.refresh`

## Entity model

- One sensor is created for each active Techem meter
- Entity naming is designed to stay stable and include the meter device ID
- The integration currently focuses on sensor readings and metadata

## Update model

- Normal updates run automatically through the integration coordinator
- Manual refresh is optional and intended for debugging or verification

## Development

### Public test suite

Use the deterministic public test suite for repository and CI validation:

```bash
cd /config/repos/ha-techem
python3 -m venv .venv
. .venv/bin/activate
python3 -m pip install -r requirements_test.txt
pytest tests
```

### Local private live validation

For local beta checks against a real Techem account, use the ignored local setup:

- `tests_local/live.env`
- `python3 tests_local/run_live_smoke.py`

The private live workflow is intentionally kept outside the public user-facing
README because it is for maintainers and local beta validation, not for normal
users of the integration.

## Versioning

This project now keeps explicit versions.

Rules:

- Start at `0.1.0`
- Keep the current version in:
  - `custom_components/techem/manifest.json`
- Record user-visible changes in:
  - `CHANGELOG.md`
- Publish tagged versions as:
  - GitHub Releases from tags like `v0.1.0`

Suggested versioning style:

- `0.x.y` while the project is still in beta
- bump the patch version for fixes and small improvements
- bump the minor version for larger user-visible feature additions or migration changes

## Release checklist

1. Update `custom_components/techem/manifest.json`
2. Update `CHANGELOG.md`
3. Run:
   - `pytest tests`
   - `python3 tests_local/run_live_smoke.py`
4. Commit
5. Push `main`
6. Create and push a matching git tag:
   - `git tag vX.Y.Z`
   - `git push origin vX.Y.Z`
7. GitHub Actions will:
   - validate that the tag matches `manifest.json`
   - run `ruff` and `pytest`
   - create the GitHub Release using the matching `CHANGELOG.md` section
