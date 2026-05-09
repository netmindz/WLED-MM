"""
GET endpoint tests — schema validation
=======================================
All read-only endpoints are tested here. Responses are validated against
the OpenAPI schemas using jsonschema. Schemathesis is also wired in as a
separate test class for property-based coverage.

These tests do not modify device state.
"""

import pytest
import schemathesis

# ─── Schema-driven tests via Schemathesis ─────────────────────────────────────

# Load the spec once at module level. `base_url` is overridden per-session
# by the `schema` fixture below.
schema = schemathesis.from_file(
    "openapi.yaml",
    base_url=None,  # overridden in fixture
)


@pytest.fixture(scope="module")
def schemathesis_schema(base_url):
    return schemathesis.from_file("openapi.yaml", base_url=base_url)


@schemathesis.parametrize()
class TestSchemaGetEndpoints:
    """
    Auto-generated tests from the OpenAPI spec for all GET endpoints.
    Schemathesis will:
      - Generate valid requests for every GET path
      - Validate that responses match the declared response schema
      - Check for 5xx errors
    """

    # Exclude endpoints that require auth or are UI pages
    # (those are covered in dedicated test files)
    EXCLUDE_PATHS = {
        "/edit",
        "/upload",
        "/update",
        "/updatebootloader",
        "/settings",
        "/",
        "/liveview",
        "/teapot",
    }

    @schema.parametrize(method="GET")
    def test_get_endpoints(self, case, client):
        if case.path in self.EXCLUDE_PATHS:
            pytest.skip(f"Skipping UI/auth endpoint: {case.path}")
        response = case.call(session=client)
        case.validate_response(response)


# ─── Explicit GET tests with assertions ───────────────────────────────────────

class TestJsonState:
    def test_returns_200(self, client):
        resp = client.get("/json/state")
        assert resp.status_code == 200

    def test_content_type_json(self, client):
        resp = client.get("/json/state")
        assert "application/json" in resp.headers["content-type"]

    def test_has_required_fields(self, client):
        data = client.get("/json/state").json()
        assert "on" in data
        assert "bri" in data
        assert "seg" in data
        assert isinstance(data["seg"], list)
        assert len(data["seg"]) >= 1

    def test_bri_in_range(self, client):
        data = client.get("/json/state").json()
        assert 0 <= data["bri"] <= 255

    def test_on_is_bool(self, client):
        data = client.get("/json/state").json()
        assert isinstance(data["on"], bool)

    def test_seg_has_required_fields(self, client):
        seg = client.get("/json/state").json()["seg"][0]
        for field in ("id", "start", "stop", "on", "bri", "fx", "sx", "ix", "pal", "col"):
            assert field in seg, f"Segment missing field: {field}"

    def test_seg_col_structure(self, client):
        seg = client.get("/json/state").json()["seg"][0]
        col = seg["col"]
        assert isinstance(col, list)
        assert len(col) == 3
        for color in col:
            assert isinstance(color, list)
            assert len(color) in (3, 4)
            for channel in color:
                assert 0 <= channel <= 255

    def test_nl_object_present(self, client):
        data = client.get("/json/state").json()
        assert "nl" in data
        nl = data["nl"]
        assert "on" in nl
        assert "dur" in nl
        assert "mode" in nl
        assert "tbri" in nl
        assert isinstance(nl["on"], bool)
        assert 1 <= nl["dur"] <= 255
        assert 0 <= nl["mode"] <= 3
        assert 0 <= nl["tbri"] <= 255

    def test_udpn_object_present(self, client):
        data = client.get("/json/state").json()
        assert "udpn" in data
        udpn = data["udpn"]
        assert "send" in udpn
        assert "recv" in udpn


class TestJsonInfo:
    def test_returns_200(self, client):
        resp = client.get("/json/info")
        assert resp.status_code == 200

    def test_has_required_fields(self, client):
        data = client.get("/json/info").json()
        for field in ("ver", "vid", "leds", "name", "fxcount", "palcount",
                      "arch", "core", "freeheap", "uptime", "mac"):
            assert field in data, f"Info missing field: {field}"

    def test_ver_is_string(self, client):
        data = client.get("/json/info").json()
        assert isinstance(data["ver"], str)
        assert len(data["ver"]) > 0

    def test_vid_is_int(self, client):
        data = client.get("/json/info").json()
        assert isinstance(data["vid"], int)

    def test_leds_object(self, client):
        leds = client.get("/json/info").json()["leds"]
        assert "count" in leds
        assert "pwr" in leds
        assert "fps" in leds
        assert "maxpwr" in leds
        assert "maxseg" in leds
        assert leds["count"] >= 1
        assert leds["fps"] >= 0

    def test_fxcount_positive(self, client):
        data = client.get("/json/info").json()
        assert data["fxcount"] > 0

    def test_palcount_positive(self, client):
        data = client.get("/json/info").json()
        assert data["palcount"] > 0

    def test_freeheap_reasonable(self, client):
        # Warn if heap is critically low (< 10KB)
        data = client.get("/json/info").json()
        freeheap = data["freeheap"]
        assert freeheap > 0
        if freeheap < 10_000:
            pytest.warns(
                UserWarning,
                match="Free heap is critically low",
            )

    def test_wifi_object(self, client):
        data = client.get("/json/info").json()
        if "wifi" in data:
            wifi = data["wifi"]
            assert "bssid" in wifi
            assert "signal" in wifi
            assert 0 <= wifi["signal"] <= 100

    def test_fs_object(self, client):
        data = client.get("/json/info").json()
        if "fs" in data:
            fs = data["fs"]
            assert "u" in fs
            assert "t" in fs
            assert fs["u"] <= fs["t"]


class TestJsonFull:
    def test_returns_all_sections(self, client):
        data = client.get("/json").json()
        assert "state" in data
        assert "info" in data
        assert "effects" in data
        assert "palettes" in data

    def test_effects_is_array_of_strings(self, client):
        effects = client.get("/json").json()["effects"]
        assert isinstance(effects, list)
        assert len(effects) > 0
        assert all(isinstance(e, str) for e in effects)

    def test_palettes_is_array_of_strings(self, client):
        palettes = client.get("/json").json()["palettes"]
        assert isinstance(palettes, list)
        assert len(palettes) > 0
        assert all(isinstance(p, str) for p in palettes)

    def test_effects_count_matches_info(self, client):
        data = client.get("/json").json()
        assert len(data["effects"]) == data["info"]["fxcount"]

    def test_palettes_count_matches_info(self, client):
        data = client.get("/json").json()
        assert len(data["palettes"]) == data["info"]["palcount"]


class TestJsonSi:
    def test_returns_state_and_info(self, client):
        data = client.get("/json/si").json()
        assert "state" in data
        assert "info" in data
        # Should NOT include effects/palettes arrays
        assert "effects" not in data
        assert "palettes" not in data


class TestJsonEffects:
    def test_returns_array(self, client):
        data = client.get("/json/effects").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_first_effect_is_solid(self, client):
        # Effect 0 is always "Solid"
        effects = client.get("/json/effects").json()
        assert effects[0] == "Solid"


class TestJsonPalettes:
    def test_returns_array(self, client):
        data = client.get("/json/palettes").json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_first_palette_is_default(self, client):
        palettes = client.get("/json/palettes").json()
        assert palettes[0] == "Default"


class TestJsonPalx:
    def test_page_0_returns_data(self, client):
        data = client.get("/json/palx?page=0").json()
        assert "m" in data
        assert "p" in data
        assert isinstance(data["m"], int)
        assert isinstance(data["p"], dict)

    def test_page_out_of_range_returns_empty(self, client):
        data = client.get("/json/palx?page=999").json()
        assert "p" in data
        assert data["p"] == {}

    def test_palette_color_stops_structure(self, client):
        data = client.get("/json/palx?page=0").json()
        for pal_id, stops in data["p"].items():
            assert isinstance(stops, list), f"Palette {pal_id} stops not a list"
            for stop in stops:
                if isinstance(stop, list):
                    assert len(stop) == 4, f"Palette {pal_id} stop not 4 elements"
                elif stop == "r":
                    pass  # random marker
                else:
                    pytest.fail(f"Unexpected stop format in palette {pal_id}: {stop}")


class TestJsonFxData:
    def test_returns_array(self, client):
        data = client.get("/json/fxdata").json()
        assert isinstance(data, list)

    def test_length_matches_fxcount(self, client, fx_count):
        data = client.get("/json/fxdata").json()
        assert len(data) == fx_count

    def test_entries_are_strings(self, client):
        data = client.get("/json/fxdata").json()
        assert all(isinstance(entry, str) for entry in data)


class TestJsonNodes:
    def test_returns_nodes_key(self, client):
        data = client.get("/json/nodes").json()
        assert "nodes" in data
        assert isinstance(data["nodes"], list)

    def test_node_structure(self, client):
        nodes = client.get("/json/nodes").json()["nodes"]
        for node in nodes:
            assert "name" in node
            assert "ip" in node
            assert "age" in node


class TestJsonNetworks:
    def test_returns_networks_key(self, client):
        data = client.get("/json/networks").json()
        assert "networks" in data
        assert isinstance(data["networks"], list)

    def test_network_structure(self, client):
        networks = client.get("/json/networks").json()["networks"]
        for network in networks:
            assert "ssid" in network
            assert "rssi" in network
            assert "channel" in network


class TestJsonPins:
    def test_returns_pins_key(self, client):
        data = client.get("/json/pins").json()
        assert "pins" in data
        assert isinstance(data["pins"], list)

    def test_pin_structure(self, client):
        pins = client.get("/json/pins").json()["pins"]
        for pin in pins:
            assert "p" in pin   # GPIO number
            assert "a" in pin   # allocated


class TestSystemEndpoints:
    def test_version_returns_int_string(self, client):
        resp = client.get("/version")
        assert resp.status_code == 200
        assert resp.text.strip().isdigit()

    def test_uptime_returns_int_string(self, client):
        resp = client.get("/uptime")
        assert resp.status_code == 200
        assert resp.text.strip().isdigit()

    def test_freeheap_returns_int_string(self, client):
        resp = client.get("/freeheap")
        assert resp.status_code == 200
        assert resp.text.strip().isdigit()

    def test_teapot(self, client):
        resp = client.get("/teapot")
        assert resp.status_code == 418
