# WLED Integration Tests

Integration test suite for the WLED HTTP API. Tests run against a real
WLED device on the network and validate responses against the OpenAPI spec
in `openapi.yaml`.

## Setup

```bash
cd tests/integration
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running tests

```bash
# Basic run — skips all destructive tests
WLED_HOST=192.168.1.x pytest

# With explicit flag instead of env var
pytest --wled-host 192.168.1.x

# With a settings PIN (needed for /json/cfg POST, /edit, etc.)
WLED_HOST=192.168.1.x WLED_PIN=1234 pytest

# Run only GET endpoint tests (safest — read-only)
pytest wled_tests/test_get_endpoints.py

# Run only schema-driven schemathesis tests
pytest wled_tests/test_get_endpoints.py::TestSchemaGetEndpoints

# Include destructive tests (reboot, etc.) — use with caution
pytest --run-destructive

# Increase timeout for slow devices (ESP8266 on a busy network)
pytest --request-timeout 20

# Stop on first failure
pytest -x
```

## Schemathesis CLI (standalone schema validation)

Schemathesis can also be run directly against the OpenAPI spec without pytest:

```bash
# Validate all GET endpoints against the spec
schemathesis run ../../openapi.yaml \
  --base-url http://192.168.1.x \
  --method GET \
  --validate-schema true

# Full run including POST (will mutate state — use carefully)
schemathesis run ../../openapi.yaml \
  --base-url http://192.168.1.x \
  --exclude-path /reset \
  --exclude-path /update \
  --exclude-path /updatebootloader
```

## Test files

| File | What it tests |
|---|---|
| `conftest.py` | Fixtures: device client, state save/restore |
| `wled_tests/test_get_endpoints.py` | All GET endpoints + schemathesis schema validation |
| `wled_tests/test_state_write.py` | POST /json/state — power, brightness, transitions, UDP sync |
| `wled_tests/test_segments_presets.py` | Segment manipulation, nightlight, presets, playlists |
| `wled_tests/test_legacy_api.py` | Legacy /win HTTP API (XML responses) |
| `wled_tests/test_destructive.py` | Reboot tests (skipped by default) |

## Safety

- All state-mutating tests use the `saved_state` fixture which saves the device
  state before the test and restores it afterward.
- A session-level fixture also saves and restores state as a fallback.
- Preset slot **250** (and 248/249 for playlist tests) are used for temporary
  saves and deleted after the test. Avoid using these slot numbers for real presets
  while testing.
- Destructive tests (`--run-destructive`) will reboot the device. Ensure nothing
  depends on the device being online during the test run.

## Configuration

| Option | Env var | Default | Description |
|---|---|---|---|
| `--wled-host` | `WLED_HOST` | *(required)* | Device IP or hostname |
| `--wled-port` | — | `80` | HTTP port |
| `--wled-pin` | `WLED_PIN` | — | Settings PIN |
| `--run-destructive` | — | `false` | Enable reboot/OTA tests |
| `--request-timeout` | — | `10.0` | HTTP timeout in seconds |
