"""
WLED Integration Test Configuration
====================================
Configure the target device via environment variables or pytest options:

    WLED_HOST=192.168.1.x pytest tests/integration/
    pytest tests/integration/ --wled-host 192.168.1.x

State save/restore
------------------
The session-scoped `wled_state` fixture saves the full device state before
the test session and restores it afterward. Individual tests that modify
state should use the `saved_state` function-scoped fixture to restore after
each test.

Destructive endpoints (reboot, OTA, /reset) are excluded from the suite by
default. Pass --run-destructive to include them.
"""

import os
import time
import copy

import pytest
import httpx


# ─── CLI options ──────────────────────────────────────────────────────────────

def pytest_addoption(parser):
    parser.addoption(
        "--wled-host",
        default=None,
        help="WLED device IP or hostname (overrides WLED_HOST env var)",
    )
    parser.addoption(
        "--wled-port",
        default=80,
        type=int,
        help="WLED HTTP port (default: 80)",
    )
    parser.addoption(
        "--wled-pin",
        default=None,
        help="Settings PIN for protected endpoints (overrides WLED_PIN env var)",
    )
    parser.addoption(
        "--run-destructive",
        action="store_true",
        default=False,
        help="Include destructive tests (reboot, OTA). Use with caution.",
    )
    parser.addoption(
        "--request-timeout",
        default=10.0,
        type=float,
        help="HTTP request timeout in seconds (default: 10)",
    )


# ─── Markers ──────────────────────────────────────────────────────────────────

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "destructive: marks tests that reboot or flash the device"
    )
    config.addinivalue_line(
        "markers", "pin_required: marks tests that require a settings PIN"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests that take more than a few seconds"
    )


def pytest_collection_modifyitems(config, items):
    if not config.getoption("--run-destructive"):
        skip_destructive = pytest.mark.skip(
            reason="Skipping destructive test — pass --run-destructive to enable"
        )
        for item in items:
            if "destructive" in item.keywords:
                item.add_marker(skip_destructive)


# ─── Base fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def wled_host(request):
    host = request.config.getoption("--wled-host") or os.environ.get("WLED_HOST")
    if not host:
        pytest.skip(
            "No WLED device specified. Set WLED_HOST env var or pass --wled-host."
        )
    return host


@pytest.fixture(scope="session")
def wled_port(request):
    return request.config.getoption("--wled-port")


@pytest.fixture(scope="session")
def wled_pin(request):
    return request.config.getoption("--wled-pin") or os.environ.get("WLED_PIN")


@pytest.fixture(scope="session")
def request_timeout(request):
    return request.config.getoption("--request-timeout")


@pytest.fixture(scope="session")
def base_url(wled_host, wled_port):
    return f"http://{wled_host}:{wled_port}" if wled_port != 80 else f"http://{wled_host}"


@pytest.fixture(scope="session")
def client(base_url, request_timeout):
    """
    Long-lived httpx client for the test session.
    Uses a short connect timeout but a longer read timeout to accommodate
    ESP8266/ESP32 response times.
    """
    with httpx.Client(
        base_url=base_url,
        timeout=httpx.Timeout(request_timeout, connect=5.0),
        headers={"Content-Type": "application/json"},
    ) as c:
        # Verify device is reachable before running any tests
        try:
            resp = c.get("/json/info")
            resp.raise_for_status()
        except Exception as exc:
            pytest.skip(f"WLED device at {base_url} is not reachable: {exc}")
        yield c


# ─── State save/restore ────────────────────────────────────────────────────────

def _fetch_state(client):
    resp = client.get("/json/state")
    resp.raise_for_status()
    return resp.json()


def _apply_state(client, state):
    """
    Restore device state. We send the minimal fields needed to restore
    appearance without touching segments (which may have changed count).
    """
    restore = {
        "on": state["on"],
        "bri": state["bri"],
        "transition": state.get("transition", 7),
        "nl": state.get("nl", {}),
        "seg": state.get("seg", []),
    }
    client.post("/json/state", json=restore)
    # Give the device a moment to settle
    time.sleep(0.3)


@pytest.fixture(scope="session", autouse=True)
def session_state_restore(client):
    """
    Save full device state at session start, restore at session end.
    This is a safety net — individual tests should still clean up after
    themselves using the `saved_state` fixture.
    """
    original = _fetch_state(client)
    yield original
    _apply_state(client, original)


@pytest.fixture()
def saved_state(client):
    """
    Function-scoped fixture. Saves state before the test, restores it after.
    Use this in any test that mutates device state.

    Usage:
        def test_something(client, saved_state):
            client.post("/json/state", json={"bri": 50})
            ...
        # state is restored automatically after the test
    """
    state = _fetch_state(client)
    yield state
    _apply_state(client, state)


# ─── Helpers ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def device_info(client):
    """Cached device info for use in tests that need to know capabilities."""
    return client.get("/json/info").json()


@pytest.fixture(scope="session")
def supports_2d(device_info):
    """True if the device has a 2D matrix configured."""
    return "matrix" in device_info.get("leds", {})


@pytest.fixture(scope="session")
def fx_count(device_info):
    return device_info["fxcount"]


@pytest.fixture(scope="session")
def pal_count(device_info):
    return device_info["palcount"]
