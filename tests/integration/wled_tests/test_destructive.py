"""
Destructive tests
==================
These tests can reboot or otherwise disrupt the device. They are skipped by
default. Pass --run-destructive to enable them.

DO NOT run these in an automated CI pipeline unless you have a way to verify
the device comes back online after a reboot.
"""

import time
import pytest


@pytest.mark.destructive
class TestReboot:
    def test_reset_endpoint(self, client, base_url):
        """GET /reset should schedule a reboot."""
        resp = client.get("/reset")
        # Response is HTML with a confirmation message; status 200
        assert resp.status_code == 200

        # Wait for device to go offline then come back
        time.sleep(3)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                r = client.get("/json/info", timeout=3)
                if r.status_code == 200:
                    return  # Device is back
            except Exception:
                pass
            time.sleep(1)

        pytest.fail("Device did not come back online within 30s after /reset")

    def test_rb_via_json(self, client):
        """POST {"rb": true} should reboot the device."""
        resp = client.post("/json/state", json={"rb": True})
        assert resp.status_code == 200

        time.sleep(3)
        deadline = time.time() + 30
        while time.time() < deadline:
            try:
                r = client.get("/json/info", timeout=3)
                if r.status_code == 200:
                    return
            except Exception:
                pass
            time.sleep(1)

        pytest.fail("Device did not come back online within 30s after rb:true")
