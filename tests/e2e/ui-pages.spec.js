const { test, expect } = require('@playwright/test');

/**
 * Test suite for WLED web UI pages
 * Validates that all main pages load without JavaScript errors
 */

// Store console errors
let consoleErrors = [];

test.beforeEach(async ({ page }) => {
  consoleErrors = [];
  
  // Listen for console errors
  page.on('console', msg => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg.text());
    }
  });
  
  // Listen for page errors
  page.on('pageerror', error => {
    consoleErrors.push(`Page error: ${error.message}`);
  });
});

test.describe('WLED Web UI - Page Loading', () => {
  
  test('main index page loads without errors', async ({ page }) => {
    await page.goto('/');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    // Check that page title or key element exists
    await expect(page.locator('body')).toBeVisible();
    
    // Verify no JavaScript errors
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('settings page loads without errors', async ({ page }) => {
    await page.goto('/settings.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('WiFi settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_wifi.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('LED settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_leds.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('UI settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_ui.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('sync settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_sync.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('time settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_time.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('security settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_sec.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('DMX settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_dmx.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('usermods settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_um.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('2D settings page loads without errors', async ({ page }) => {
    await page.goto('/settings_2D.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
  test('update page loads without errors', async ({ page }) => {
    await page.goto('/update.htm');
    
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
});

test.describe('WLED Web UI - Navigation', () => {
  
  test('can navigate from main page to settings', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');
    
    // Look for settings link/button - adjust selector based on actual UI
    // This is a basic test that can be expanded
    await page.goto('/settings.htm');
    await page.waitForLoadState('networkidle');
    
    await expect(page.locator('body')).toBeVisible();
    expect(consoleErrors, `JavaScript errors found: ${consoleErrors.join(', ')}`).toHaveLength(0);
  });
  
});
