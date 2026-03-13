"""Tests for Techem token extraction helpers."""

from custom_components.techem.api import (
    extract_csrf_token,
    extract_portal_auth_token,
    looks_like_login_page,
)


def test_extract_portal_auth_token_from_html() -> None:
    html = '<a href="/home?p_auth=abc123XYZ">Login</a>'
    assert extract_portal_auth_token(html) == 'abc123XYZ'


def test_extract_portal_auth_token_from_liferay_escaped_html() -> None:
    html = r"<script>submitFormWithParams('p_auth\x3dxm0l8SgZ');</script>"
    assert extract_portal_auth_token(html) == "xm0l8SgZ"


def test_extract_csrf_token_from_meta_tag() -> None:
    html = '<meta name="csrf-token" content="csrf-token-1">'
    assert extract_csrf_token(html) == 'csrf-token-1'


def test_extract_csrf_token_from_script_fallback() -> None:
    html = '<script>Liferay.authToken = "csrf-token-2";</script>'
    assert extract_csrf_token(html) == 'csrf-token-2'


def test_detect_login_page() -> None:
    html = (
        "<form>"
        '<input name="_com_liferay_login_web_portlet_'
        'LoginPortlet_INSTANCE_irfelogin_login">'
        "</form>"
    )
    assert looks_like_login_page(html) is True
