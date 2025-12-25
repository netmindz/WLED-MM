# End-to-End Tests

This directory contains end-to-end tests for the WLED web UI using Playwright.

## Overview

The E2E tests validate that the WLED web interface works correctly when served from an ESP32 device. The tests use:
- **Wokwi** - ESP32 simulator that runs the actual WLED firmware
- **Playwright** - Browser automation tool for testing the web UI

## Test Structure

- `ui-pages.spec.js` - Tests that all main UI pages load without JavaScript errors

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
```

### Running the Tests

The easiest way is to use the GitHub Actions workflow, but you can also run locally:

1. Create `wokwi.toml` configuration (see workflow file for example)
2. Create `diagram.json` for ESP32 board definition
3. Start the Wokwi simulator
4. Run tests: `WLED_URL=http://localhost:8180 npm test`

## CI/CD Integration

The E2E tests run automatically on:
- Push to `mdev` or `main` branches
- Pull requests to `mdev` or `main` branches
- Manual workflow dispatch

See `.github/workflows/e2e-test.yml` for the complete workflow.

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

### JavaScript errors in tests
- Check the browser console output in the test report
- Verify the web UI was built before running tests
- Look at the Playwright HTML report for details

### Simulator doesn't start
- Check that the firmware binary exists at the expected path
- Verify Wokwi CLI is installed correctly
- Check the Wokwi logs for error messages
