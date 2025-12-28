# End-to-End Tests

This directory contains end-to-end tests for the WLED web UI using Playwright.

## Overview

The E2E tests validate that the WLED web interface works correctly when served from an ESP32 device. The tests use:
- **Wokwi CLI** - ESP32 simulator that runs the actual WLED firmware in a virtual environment
- **Playwright** - Browser automation tool for testing the web UI served by the simulated ESP32

Unlike traditional web UI tests that use a separate HTTP server, these tests connect to the actual web server running on the simulated ESP32, ensuring end-to-end validation of the firmware and web interface integration.

## Test Structure

- `ui-pages.spec.js` - Tests that all main UI pages load without JavaScript errors

## Running Tests in CI

The GitHub Actions workflow automatically:
1. Builds the WLED firmware for ESP32
2. Starts Wokwi simulator with the firmware
3. Waits for the web server to be ready on port 8180
4. Runs Playwright tests against the simulated device
5. Collects and uploads test reports

### Required Secrets

The Wokwi CLI requires a license token for CI usage. Repository administrators need to add:
- `WOKWI_CLI_TOKEN` - Wokwi CLI license token (get from https://wokwi.com/dashboard/ci)

## Running Tests Locally

### Prerequisites

1. Install dependencies:
```bash
npm ci
```

2. Build the web UI:
```bash
npm run build
```

3. Build the firmware:
```bash
pip install -r requirements.txt
pio run -e esp32dev_compat
```

4. Install Playwright browsers:
```bash
npx playwright install chromium
```

5. Install Wokwi CLI:
```bash
curl -L https://wokwi.com/ci/install.sh | sh
export PATH="$HOME/.wokwi/bin:$PATH"
```

### Running the Tests

1. Create `wokwi.toml` configuration:
```toml
[wokwi]
version = 1
elf = ".pio/build/esp32dev_compat/firmware.elf"
firmware = ".pio/build/esp32dev_compat/firmware.bin"

[[net.forward]]
host = "0.0.0.0"
guest = 80
port = 8180
```

2. Create `diagram.json` for ESP32 board:
```json
{
  "version": 1,
  "author": "WLED E2E Tests",
  "editor": "wokwi",
  "parts": [
    { 
      "type": "wokwi-esp32-devkit-v1", 
      "id": "esp", 
      "top": 0, 
      "left": 0, 
      "attrs": {} 
    }
  ],
  "connections": [],
  "dependencies": {}
}
```

3. Configure WiFi credentials for Wokwi:
```bash
# Create my_config.h to connect to Wokwi-GUEST network
cat > wled00/my_config.h << 'EOF'
#pragma once
#define CLIENT_SSID "Wokwi-GUEST"
#define CLIENT_PASS ""
EOF
```

4. Start the Wokwi simulator:
```bash
wokwi-cli --timeout 600000 .
```

5. In another terminal, run tests:
```bash
WLED_URL=http://localhost:8180 npm test
```

## Writing New Tests

To add new tests:

1. Create a new `.spec.js` file in this directory
2. Use the existing tests as examples
3. Follow the pattern of checking for JavaScript errors
4. Test should verify that pages load and key functionality works

Example:
```javascript
const { test, expect } = require('@playwright/test');

test('my new test', async ({ page }) => {
  await page.goto('/my-page.htm');
  await page.waitForLoadState('networkidle');
  await expect(page.locator('body')).toBeVisible();
});
```

## Troubleshooting

### Tests fail with connection errors
- Ensure the Wokwi simulator is running and accessible
- Check that port forwarding is configured correctly (port 8180)
- Verify the firmware built successfully
- Check Wokwi logs for startup errors

### JavaScript errors in tests
- Check the browser console output in the test report
- Verify the web UI was built before running tests (`npm run build`)
- Look at the Playwright HTML report for details
- Review the actual page source served by the simulator

### Simulator doesn't start
- Check that the firmware binary exists at `.pio/build/esp32dev_compat/firmware.elf`
- Verify Wokwi CLI is installed correctly (`which wokwi-cli`)
- Ensure you have a valid WOKWI_CLI_TOKEN set (for CI/licensed features)
- Check the Wokwi logs (`wokwi.log` in CI) for error messages

### Wokwi CLI License
- Wokwi CLI is free for individual use but requires a license for CI/CD
- Get a license from https://wokwi.com/dashboard/ci
- Add the token to GitHub Secrets as `WOKWI_CLI_TOKEN`
