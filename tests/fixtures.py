"""Collection of fixtures and helpers used in tests."""

import tempfile
from collections.abc import Generator

import pytest

import mumasp


def send_mock_cmd(cmd: str) -> str:
    """Mock implementation of Telescope.send_cmd() that can be used for testing."""
    if cmd == "?":
        return "HELP"
    if cmd == "a":
        return "0,0,0,0"
    if cmd.startswith("c"):
        return "0"
    if cmd == "e":
        return "0,0"
    if cmd.startswith("m"):
        return "0"
    if cmd == "r":
        return "2026,01,24,19,49,00"
    if cmd.startswith("s"):
        return "0"
    if cmd == "x":
        return "0"
    if cmd == "n":
        return "23"
    if cmd == "h":
        return "\n".join(["23"] + [str(i) for i in range(23)])
    return "-3"


@pytest.fixture(scope="function")
def tempdir() -> Generator[tempfile.TemporaryDirectory]:
    """Fixture for a module-wide temporary directory."""
    d = tempfile.TemporaryDirectory()
    yield d
    d.cleanup()


@pytest.fixture(scope="function")
def test_telescope() -> Generator[mumasp.Telescope]:
    """Return a Telescope instance with a mock Arduino communication."""
    t = mumasp.Telescope()
    t.send_cmd = send_mock_cmd
    yield t
