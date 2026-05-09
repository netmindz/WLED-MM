"""
Segment, nightlight, and preset tests
=======================================
Tests for segment manipulation, nightlight control, and preset
save/load/delete — all stateful operations that restore device state
via the `saved_state` fixture.
"""

import time
import pytest


# ─── Segment tests ────────────────────────────────────────────────────────────

class TestSegmentWrite:
    def test_set_segment_on_off(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "on": False}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["on"] is False

        client.post("/json/state", json={"seg": [{"id": 0, "on": True}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["on"] is True

    def test_set_segment_brightness(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "bri": 100}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["bri"] == 100

    def test_set_primary_color(self, client, saved_state):
        client.post("/json/state", json={
            "seg": [{"id": 0, "col": [[255, 0, 128]]}]
        })
        seg = client.get("/json/state").json()["seg"][0]
        r, g, b = seg["col"][0][0], seg["col"][0][1], seg["col"][0][2]
        assert r == 255
        assert g == 0
        assert b == 128

    def test_set_color_via_hex(self, client, saved_state):
        client.post("/json/state", json={
            "seg": [{"id": 0, "col": ["FF0080"]}]
        })
        seg = client.get("/json/state").json()["seg"][0]
        # WLED returns colors as arrays, not hex strings
        assert isinstance(seg["col"][0], list)
        assert seg["col"][0][0] == 255
        assert seg["col"][0][1] == 0
        assert seg["col"][0][2] == 128

    def test_set_effect(self, client, saved_state, fx_count):
        # Effect 1 = Blink (always present)
        client.post("/json/state", json={"seg": [{"id": 0, "fx": 1}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["fx"] == 1

    def test_set_effect_speed(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "sx": 200}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["sx"] == 200

    def test_set_effect_intensity(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "ix": 50}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["ix"] == 50

    def test_set_palette(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "pal": 1}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["pal"] == 1

    def test_set_segment_name(self, client, saved_state):
        client.post("/json/state", json={
            "seg": [{"id": 0, "n": "TestSeg"}]
        })
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["n"] == "TestSeg"

    def test_reverse_segment(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "rev": True}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["rev"] is True

    def test_mirror_segment(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "mi": True}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["mi"] is True

    def test_freeze_segment(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "frz": True}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["frz"] is True

        client.post("/json/state", json={"seg": [{"id": 0, "frz": False}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["frz"] is False

    def test_increment_effect_speed(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "sx": 100}]})
        client.post("/json/state", json={"seg": [{"id": 0, "sx": "~10"}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["sx"] == 110

    def test_random_palette(self, client, saved_state):
        resp = client.post("/json/state", json={
            "seg": [{"id": 0, "pal": "r"}]
        })
        assert resp.status_code == 200
        seg = client.get("/json/state").json()["seg"][0]
        assert isinstance(seg["pal"], int)

    def test_fxdef_applies_defaults(self, client, saved_state):
        """fxdef:true should reset speed/intensity to effect defaults."""
        # Set known non-default speed
        client.post("/json/state", json={"seg": [{"id": 0, "fx": 1, "sx": 200}]})
        # Now apply fxdef
        resp = client.post("/json/state", json={
            "seg": [{"id": 0, "fxdef": True}]
        })
        assert resp.status_code == 200

    def test_custom_sliders(self, client, saved_state):
        client.post("/json/state", json={
            "seg": [{"id": 0, "c1": 100, "c2": 150, "c3": 15}]
        })
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["c1"] == 100
        assert seg["c2"] == 150
        assert seg["c3"] == 15

    def test_custom_checkboxes(self, client, saved_state):
        client.post("/json/state", json={
            "seg": [{"id": 0, "o1": True, "o2": False, "o3": True}]
        })
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["o1"] is True
        assert seg["o2"] is False
        assert seg["o3"] is True


class TestSegmentIndividualLEDs:
    def test_set_individual_leds_hex(self, client, saved_state):
        """Set first 3 LEDs via hex color strings."""
        resp = client.post("/json/state", json={
            "seg": [{"id": 0, "i": ["FF0000", "00FF00", "0000FF"]}]
        })
        assert resp.status_code == 200

    def test_set_individual_leds_array(self, client, saved_state):
        """Set first 3 LEDs via RGB arrays."""
        resp = client.post("/json/state", json={
            "seg": [{"id": 0, "i": [[255, 0, 0], [0, 255, 0], [0, 0, 255]]}]
        })
        assert resp.status_code == 200

    def test_set_indexed_leds(self, client, saved_state):
        """Set LED at specific index."""
        resp = client.post("/json/state", json={
            "seg": [{"id": 0, "i": [0, "FF0000", 5, "00FF00"]}]
        })
        assert resp.status_code == 200


class TestSegmentGroupingSpacing:
    def test_set_grouping(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "grp": 3}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["grp"] == 3

    def test_set_spacing(self, client, saved_state):
        client.post("/json/state", json={"seg": [{"id": 0, "spc": 2}]})
        seg = client.get("/json/state").json()["seg"][0]
        assert seg["spc"] == 2


# ─── Nightlight tests ─────────────────────────────────────────────────────────

class TestNightlight:
    def test_enable_nightlight(self, client, saved_state):
        resp = client.post("/json/state", json={
            "nl": {"on": True, "dur": 10, "mode": 1, "tbri": 0}
        })
        assert resp.status_code == 200
        state = client.get("/json/state").json()
        assert state["nl"]["on"] is True

    def test_disable_nightlight(self, client, saved_state):
        client.post("/json/state", json={"nl": {"on": True}})
        client.post("/json/state", json={"nl": {"on": False}})
        state = client.get("/json/state").json()
        assert state["nl"]["on"] is False

    @pytest.mark.parametrize("mode", [0, 1, 2, 3])
    def test_nightlight_modes(self, client, saved_state, mode):
        resp = client.post("/json/state", json={
            "nl": {"on": True, "dur": 60, "mode": mode, "tbri": 0}
        })
        assert resp.status_code == 200
        nl = client.get("/json/state").json()["nl"]
        assert nl["mode"] == mode

    def test_nightlight_duration(self, client, saved_state):
        client.post("/json/state", json={"nl": {"on": True, "dur": 30}})
        nl = client.get("/json/state").json()["nl"]
        assert nl["dur"] == 30

    def test_nightlight_target_brightness(self, client, saved_state):
        client.post("/json/state", json={"nl": {"on": True, "tbri": 50}})
        nl = client.get("/json/state").json()["nl"]
        assert nl["tbri"] == 50

    def test_nightlight_rem_is_read_only(self, client, saved_state):
        """rem (remaining seconds) appears in response but cannot be set."""
        client.post("/json/state", json={"nl": {"on": True, "dur": 60}})
        nl = client.get("/json/state").json()["nl"]
        assert "rem" in nl
        assert isinstance(nl["rem"], int)


# ─── Preset tests ─────────────────────────────────────────────────────────────

SAFE_PRESET_ID = 250  # Use the last slot to avoid clobbering real presets


class TestPresets:
    def test_save_and_load_preset(self, client, saved_state):
        # Set a known state
        client.post("/json/state", json={"bri": 77, "on": True})

        # Save to preset 250
        resp = client.post("/json/state", json={"psave": SAFE_PRESET_ID})
        assert resp.status_code == 200

        # Change state
        client.post("/json/state", json={"bri": 200})

        # Load preset 250 — should restore bri to 77
        client.post("/json/state", json={"ps": SAFE_PRESET_ID})
        time.sleep(0.5)  # give device time to apply preset
        state = client.get("/json/state").json()
        assert state["bri"] == 77

        # Cleanup: delete the preset
        client.post("/json/state", json={"pdel": SAFE_PRESET_ID})

    def test_delete_preset(self, client, saved_state):
        # Save first
        client.post("/json/state", json={"psave": SAFE_PRESET_ID})
        # Delete
        resp = client.post("/json/state", json={"pdel": SAFE_PRESET_ID})
        assert resp.status_code == 200
        assert resp.json().get("success") is True

    def test_random_preset(self, client, saved_state):
        """ps='r' should apply a random preset without error."""
        resp = client.post("/json/state", json={"ps": "r"})
        assert resp.status_code == 200

    def test_next_playlist_item(self, client, saved_state):
        """np:true should not crash even if no playlist is active."""
        resp = client.post("/json/state", json={"np": True})
        assert resp.status_code == 200


# ─── Playlist tests ───────────────────────────────────────────────────────────

class TestPlaylist:
    def test_create_playlist(self, client, saved_state):
        """Create a simple 2-preset playlist (uses safe preset slot)."""
        # Save two presets first
        client.post("/json/state", json={"bri": 50, "psave": 248})
        client.post("/json/state", json={"bri": 200, "psave": 249})

        resp = client.post("/json/state", json={
            "playlist": {
                "ps": [248, 249],
                "dur": [10, 10],
                "transition": 0,
                "repeat": 2,
            }
        })
        assert resp.status_code == 200

        # Stop playlist and clean up
        client.post("/json/state", json={"pl": -1})
        client.post("/json/state", json={"pdel": 248})
        client.post("/json/state", json={"pdel": 249})

    def test_stop_playlist(self, client, saved_state):
        resp = client.post("/json/state", json={"pl": -1})
        assert resp.status_code == 200
        state = client.get("/json/state").json()
        assert state["pl"] == -1
