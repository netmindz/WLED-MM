"""
Legacy HTTP API (/win) tests
==============================
Tests for the legacy query-string HTTP API. Returns XML responses.
Uses the `saved_state` fixture for state-mutating tests.
"""

import pytest
from xml.etree import ElementTree


def get_xml(client, params=""):
    """GET /win with the given query string and parse the XML response."""
    resp = client.get(f"/win{params}")
    assert resp.status_code == 200
    assert "xml" in resp.headers.get("content-type", "").lower() or \
           resp.text.strip().startswith("<?xml")
    return ElementTree.fromstring(resp.text)


def xml_int(root: ElementTree.Element, tag: str) -> int:
    """Find a tag in an XML element and return its text as int. Fails if missing."""
    el = root.find(tag)
    assert el is not None, f"XML element <{tag}> not found"
    assert el.text is not None, f"XML element <{tag}> has no text"
    return int(el.text)


class TestWinApiRead:
    def test_returns_xml(self, client):
        resp = client.get("/win")
        assert resp.status_code == 200
        assert resp.text.strip().startswith("<?xml")

    def test_xml_has_vs_root(self, client):
        root = get_xml(client)
        assert root.tag == "vs"

    def test_xml_has_brightness(self, client):
        root = get_xml(client)
        bri = xml_int(root, "ac")
        assert 0 <= bri <= 255

    def test_xml_has_primary_color(self, client):
        root = get_xml(client)
        cl_elements = root.findall("cl")
        assert len(cl_elements) == 3  # R, G, B
        for el in cl_elements:
            assert el.text is not None
            assert 0 <= int(el.text) <= 255

    def test_xml_has_secondary_color(self, client):
        root = get_xml(client)
        cs_elements = root.findall("cs")
        assert len(cs_elements) == 3  # R, G, B

    def test_xml_has_effect_fields(self, client):
        root = get_xml(client)
        assert root.find("fx") is not None
        assert root.find("sx") is not None
        assert root.find("ix") is not None
        assert root.find("fp") is not None


class TestWinApiWrite:
    def test_set_brightness(self, client, saved_state):
        get_xml(client, "&A=100")
        state = client.get("/json/state").json()
        assert state["bri"] == 100

    def test_turn_on(self, client, saved_state):
        client.post("/json/state", json={"on": False})
        get_xml(client, "&T=1")
        state = client.get("/json/state").json()
        assert state["on"] is True

    def test_turn_off(self, client, saved_state):
        client.post("/json/state", json={"on": True})
        get_xml(client, "&T=0")
        state = client.get("/json/state").json()
        assert state["on"] is False

    def test_toggle(self, client, saved_state):
        before = client.get("/json/state").json()["on"]
        get_xml(client, "&T=2")
        after = client.get("/json/state").json()["on"]
        assert after is not before

    def test_set_primary_color(self, client, saved_state):
        get_xml(client, "&R=255&G=0&B=128")
        state = client.get("/json/state").json()
        col = state["seg"][0]["col"][0]
        assert col[0] == 255
        assert col[1] == 0
        assert col[2] == 128

    def test_set_primary_color_hex(self, client, saved_state):
        get_xml(client, "&CL=FF0080")
        state = client.get("/json/state").json()
        col = state["seg"][0]["col"][0]
        assert col[0] == 255
        assert col[1] == 0
        assert col[2] == 128

    def test_set_effect(self, client, saved_state):
        get_xml(client, "&FX=1")
        state = client.get("/json/state").json()
        assert state["seg"][0]["fx"] == 1

    def test_set_speed(self, client, saved_state):
        get_xml(client, "&SX=200")
        state = client.get("/json/state").json()
        assert state["seg"][0]["sx"] == 200

    def test_set_intensity(self, client, saved_state):
        get_xml(client, "&IX=50")
        state = client.get("/json/state").json()
        assert state["seg"][0]["ix"] == 50

    def test_set_palette(self, client, saved_state):
        get_xml(client, "&FP=1")
        state = client.get("/json/state").json()
        assert state["seg"][0]["pal"] == 1

    def test_combined_params(self, client, saved_state):
        """Multiple parameters in one request."""
        get_xml(client, "&A=150&R=0&G=200&B=50&FX=0")
        state = client.get("/json/state").json()
        assert state["bri"] == 150

    def test_response_reflects_new_state(self, client, saved_state):
        """XML response from /win should reflect the state just set."""
        root = get_xml(client, "&A=77")
        ac = xml_int(root, "ac")
        assert ac == 77

    def test_nightlight_on(self, client, saved_state):
        get_xml(client, "&NL=10")  # 10 minutes
        state = client.get("/json/state").json()
        assert state["nl"]["on"] is True
        assert state["nl"]["dur"] == 10

    def test_nightlight_off(self, client, saved_state):
        get_xml(client, "&NL=10")
        get_xml(client, "&NL=0")
        state = client.get("/json/state").json()
        assert state["nl"]["on"] is False
