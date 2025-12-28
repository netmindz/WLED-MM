# End-to-End Testing

This document explains the end-to-end (E2E) testing setup for WLED using ESP32 emulation.

## Overview

WLED now includes automated end-to-end tests that verify the web interface works correctly when served from an actual ESP32 device (simulated). This is different from traditional web UI tests because:

1. **Real Firmware**: Tests run against actual compiled ESP32 firmware, not a mock server
2. **True Integration**: Tests verify the full stack - from ESP32 web server to browser rendering
3. **Production-like**: The simulated environment closely matches real hardware behavior

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                    GitHub Actions Workflow                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Build Web UI (npm run build)                            │
│     └─> Generates html_*.h files                            │
│                                                               │
│  2. Build ESP32 Firmware (pio run)                          │
│     └─> Creates firmware.elf and firmware.bin               │
│                                                               │
│  3. Start Wokwi Simulator                                   │
│     ├─> Emulates ESP32 hardware                             │
│     ├─> Runs the compiled firmware                          │
│     ├─> Starts WiFi AP / Web Server                         │
│     └─> Forwards port 80 to host port 8180                  │
│                                                               │
│  4. Run Playwright Tests                                     │
│     ├─> Opens Chromium browser                              │
│     ├─> Navigates to http://localhost:8180                  │
│     ├─> Tests all UI pages                                  │
│     └─> Verifies no JavaScript errors                       │
│                                                               │
│  5. Collect Results                                          │
│     ├─> HTML test reports                                   │
│     ├─> Screenshots on failure                              │
│     └─> Simulator logs                                      │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components

### Wokwi ESP32 Simulator
- Accurately emulates ESP32 hardware
- Supports network port forwarding
- Runs actual compiled firmware
- Provides console output and debugging

### Playwright
- Modern browser automation framework
- Captures JavaScript errors
- Takes screenshots on failure
- Generates detailed HTML reports

## Running Tests

### In CI (Automatic)

Tests run automatically on:
- Pushes to `mdev` or `main` branches
- Pull requests targeting these branches
- Manual workflow dispatch

### Locally

See [tests/e2e/README.md](../tests/e2e/README.md) for detailed instructions.

Quick start:
```bash
# Install dependencies
npm ci
pip install -r requirements.txt

# Configure WiFi for Wokwi
cat > wled00/my_config.h << 'EOF'
#pragma once
#define CLIENT_SSID "Wokwi-GUEST"
#define CLIENT_PASS ""
EOF

# Build everything
npm run build
pio run -e esp32dev_compat

# Run tests
npm test
```

## What Gets Tested

Current test coverage includes:
- ✅ Main index page loads without errors
- ✅ All settings pages load without errors
  - WiFi settings
  - LED settings  
  - UI settings
  - Sync settings
  - Time settings
  - Security settings
  - DMX settings
  - Usermod settings
  - 2D settings
- ✅ Update page loads without errors
- ✅ No JavaScript console errors on any page
- ✅ Basic navigation between pages

Future enhancements could include:
- API endpoint testing
- WebSocket functionality
- Form submissions
- Effect activation
- Real-time updates

## Configuration

### Required Secrets (for CI)

The GitHub Actions workflow requires:
- `WOKWI_CLI_TOKEN` - License token for Wokwi CLI (get from https://wokwi.com/dashboard/ci)

Repository administrators can add this in Settings → Secrets and variables → Actions.

### Firmware Target

Currently uses `esp32dev_compat` environment for testing as it:
- Builds quickly
- Is a standard ESP32 configuration
- Works well with Wokwi emulator
- Represents a common use case

## Troubleshooting

### Workflow Fails on "Start ESP32 simulator"
- Check that firmware built successfully
- Verify Wokwi token is configured
- Look at simulator logs in artifacts

### Tests Fail with "Page Error"
- Check Playwright report artifact
- Look for JavaScript console errors
- Verify web UI was built correctly

### Port 8180 Not Responding
- Simulator may need more time to start
- Check wokwi.log in artifacts
- Verify port forwarding configuration

## Future Improvements

Potential enhancements:
1. Test with Ethernet-enabled builds
2. Add API endpoint testing
3. Test WebSocket connections
4. Verify LED effect rendering
5. Test preset/playlist functionality
6. Add performance benchmarks
7. Test with different ESP32 variants (S2, S3, C3)

## Contributing

To add new tests:
1. Create test file in `tests/e2e/`
2. Follow existing patterns
3. Document what's being tested
4. Ensure tests are reliable and fast

See [../tests/e2e/README.md](../tests/e2e/README.md) for more details.
