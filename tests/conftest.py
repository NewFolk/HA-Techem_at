"""Shared pytest fixtures for Techem tests."""

from __future__ import annotations

import pytest
from _pytest.fixtures import FixtureLookupError


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(request):
    """Enable loading custom integrations in tests."""

    try:
        request.getfixturevalue("enable_custom_integrations")
    except FixtureLookupError:
        # Some local pytest environments do not expose this helper fixture.
        # The Techem tests themselves do not depend on its return value.
        pass

    yield
