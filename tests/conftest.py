"""Pytest configuration and shared fixtures."""

import pytest


@pytest.fixture(autouse=True)
def reset_environment(monkeypatch):
    """Reset environment variables for each test."""
    # This fixture runs automatically for all tests
    # Add any environment cleanup here if needed
    pass
