"""Exceptions for the Techem integration."""

from __future__ import annotations


class TechemError(Exception):
    """Base exception for Techem errors."""


class TechemApiError(TechemError):
    """Raised when the Techem API returns an unexpected result."""


class TechemAuthError(TechemApiError):
    """Raised when Techem authentication fails."""


class TechemParseError(TechemApiError):
    """Raised when Techem data cannot be parsed."""
