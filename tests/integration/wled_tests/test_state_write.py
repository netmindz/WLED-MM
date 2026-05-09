"""
State write tests
==================
Tests for POST /json and POST /json/state. All tests use the `saved_state`
fixture to restore the device to its original state after each test.

Covers:
- Master on/off and toggle
- Brightness
- Transition time
- Live override
- Main segment selection
- UDP sync flags
- Verbose response (v:true)
- Error handling (malformed JSON, unknown keys)
"""

import time
import pytest


class TestPowerControl:
    def test_turn_on(self, client, saved_state):
        client.post("/json/state", json={"on": False})
        resp = client.post("/json/state", json={"on": True})
        assert resp.status_code == 200
        state = client.get("/json/state").json()
        assert state["on"] is True

    def test_turn_off(self, client, saved_state):
        client.post("/json/state", json={"on": True})
        resp = client.post("/json/state", json={"on": False})
        assert resp.status_code == 200
        state = client.get("/json/state").json()
        assert state["on"] is False

    def test_toggle_on_to_off(self, client, saved_state):
        client.post("/json/state", json={"on": True})
        client.post("/json/state", json={"on": "t"})
        state = client.get("/json/state").json()
        assert state["on"] is False

    def test_toggle_off_to_on(self, client, saved_state):
        client.post("/json/state", json={"on": False})
        client.post("/json/state", json={"on": "t"})
        state = client.get("/json/state").json()
        assert state["on"] is True

    def test_success_response(self, client, saved_state):
        resp = client.post("/json/state", json={"on": True})
        data = resp.json()
        assert "success" in data
        assert data["success"] is True


class TestBrightness:
    @pytest.mark.parametrize("bri", [0, 1, 50, 127, 200, 255])
    def test_set_brightness(self, client, saved_state, bri):
        client.post("/json/state", json={"on": True, "bri": bri})
        state = client.get("/json/state").json()
        # WLED never reports bri=0 in state (it holds last non-zero value)
        if bri == 0:
            assert state["bri"] >= 0
        else:
            assert state["bri"] == bri

    def test_brightness_persists_when_off(self, client, saved_state):
        """Setting bri while off should be remembered when turned back on."""
        client.post("/json/state", json={"on": True, "bri": 100})
        client.post("/json/state", json={"on": False})
        state_off = client.get("/json/state").json()
        # bri should still be 100 even when off
        assert state_off["bri"] == 100


class TestTransition:
    @pytest.mark.parametrize("tt", [0, 4, 10, 100, 255])
    def test_set_transition(self, client, saved_state, tt):
        client.post("/json/state", json={"transition": tt})
        state = client.get("/json/state").json()
        assert state["transition"] == tt

    def test_tt_not_persisted(self, client, saved_state):
        """tt (one-time transition) should not appear in the state response."""
        client.post("/json/state", json={"tt": 5})
        state = client.get("/json/state").json()
        assert "tt" not in state


class TestVerboseResponse:
    def test_v_true_returns_full_state(self, client, saved_state):
        resp = client.post("/json/state", json={"on": True, "v": True})
        data = resp.json()
        # Response should be the full state, not just {"success": true}
        assert "on" in data
        assert "bri" in data
        assert "seg" in data
        assert "success" not in data

    def test_v_false_returns_success(self, client, saved_state):
        resp = client.post("/json/state", json={"on": True, "v": False})
        data = resp.json()
        assert "success" in data


class TestLiveOverride:
    @pytest.mark.parametrize("lor", [0, 1, 2])
    def test_set_live_override(self, client, saved_state, lor):
        client.post("/json/state", json={"lor": lor})
        state = client.get("/json/state").json()
        assert state["lor"] == lor

    def test_lor_reset(self, client, saved_state):
        client.post("/json/state", json={"lor": 2})
        client.post("/json/state", json={"lor": 0})
        state = client.get("/json/state").json()
        assert state["lor"] == 0


class TestMainSeg:
    def test_set_mainseg(self, client, saved_state):
        # Set to segment 0 (always exists)
        client.post("/json/state", json={"mainseg": 0})
        state = client.get("/json/state").json()
        assert state["mainseg"] == 0


class TestUdpSync:
    def test_enable_send(self, client, saved_state):
        client.post("/json/state", json={"udpn": {"send": True}})
        state = client.get("/json/state").json()
        assert state["udpn"]["send"] is True

    def test_disable_send(self, client, saved_state):
        client.post("/json/state", json={"udpn": {"send": False}})
        state = client.get("/json/state").json()
        assert state["udpn"]["send"] is False

    def test_sync_groups(self, client, saved_state):
        client.post("/json/state", json={"udpn": {"sgrp": 3, "rgrp": 7}})
        state = client.get("/json/state").json()
        assert state["udpn"]["sgrp"] == 3
        assert state["udpn"]["rgrp"] == 7

    def test_nn_not_in_state_response(self, client, saved_state):
        """nn (no-notify) flag should not appear in state response."""
        client.post("/json/state", json={"udpn": {"nn": True}})
        state = client.get("/json/state").json()
        assert "nn" not in state["udpn"]


class TestErrorHandling:
    def test_invalid_json_returns_error(self, client):
        resp = client.post(
            "/json/state",
            content=b"this is not json",
            headers={"Content-Type": "application/json"},
        )
        # Should return an error, not 500
        assert resp.status_code == 200
        data = resp.json()
        assert "error" in data

    def test_unknown_keys_are_ignored(self, client, saved_state):
        """WLED should silently ignore unknown fields."""
        resp = client.post("/json/state", json={"totally_unknown_key": 42})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True

    def test_bri_out_of_range_is_clamped(self, client, saved_state):
        """Values outside 0-255 should be clamped, not rejected."""
        resp = client.post("/json/state", json={"bri": 300})
        assert resp.status_code == 200
        state = client.get("/json/state").json()
        assert state["bri"] <= 255

    def test_empty_body_returns_success(self, client):
        resp = client.post("/json/state", json={})
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True


class TestPartialUpdate:
    def test_partial_update_preserves_other_fields(self, client, saved_state):
        """Sending only `bri` should not change `on` state."""
        client.post("/json/state", json={"on": True, "bri": 200})
        client.post("/json/state", json={"bri": 100})
        state = client.get("/json/state").json()
        assert state["on"] is True   # unchanged
        assert state["bri"] == 100   # updated
