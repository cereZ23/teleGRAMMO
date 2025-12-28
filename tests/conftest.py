"""Pytest configuration and fixtures."""
import pytest


@pytest.fixture(scope="session")
def anyio_backend():
    """Use asyncio backend for tests."""
    return "asyncio"
