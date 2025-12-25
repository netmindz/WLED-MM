# Alternative ESP32 Emulation Approaches

This document describes alternative approaches for ESP32 emulation in CI if Wokwi CLI is not suitable for your use case.

## Current Approach: Wokwi CLI

**Pros:**
- Easy to set up in CI
- Good network support with port forwarding
- Accurate ESP32 emulation
- Good documentation

**Cons:**
- Requires license/token for CI usage
- Proprietary solution
- May have usage limits

## Alternative 1: ESP32 QEMU

The Espressif fork of QEMU supports ESP32 emulation.

**Setup:**
```bash
# Clone and build ESP32 QEMU
git clone https://github.com/espressif/qemu
cd qemu
./configure --target-list=xtensa-softmmu --enable-debug --enable-sanitizers
make -j$(nproc)

# Run with firmware
./qemu-system-xtensa -nographic -machine esp32 -drive file=firmware.bin,if=mtd,format=raw
```

**Pros:**
- Open source
- No licensing costs
- Official Espressif support

**Cons:**
- More complex setup
- Network configuration is harder
- May require custom network setup for web server access

## Alternative 2: Renode

Renode is an open-source simulation framework that supports ESP32.

**Setup:**
```bash
# Install Renode
wget https://github.com/renode/renode/releases/download/v1.14.0/renode-1.14.0.linux-portable.tar.gz
tar xzf renode-1.14.0.linux-portable.tar.gz

# Create Renode script
cat > wled-test.resc << 'EOF'
mach create
machine LoadPlatformDescription @platforms/cpus/esp32.repl
sysbus LoadELF @firmware.elf
showAnalyzer sysbus.uart0
start
EOF

# Run
./renode/renode wled-test.resc
```

**Pros:**
- Open source
- Good debugging capabilities
- Network simulation possible

**Cons:**
- Complex network configuration
- Requires learning Renode scripting
- May not be as accurate as QEMU

## Alternative 3: ESP-IDF Unit Testing Framework

For API-only testing (no browser UI testing), use ESP-IDF's built-in testing.

**Setup:**
```c
// In test file
#include "unity.h"

TEST_CASE("web server responds", "[webserver]") {
    // Start server
    // Make HTTP request
    // Verify response
    TEST_ASSERT(response_ok);
}
```

**Pros:**
- Built into ESP-IDF
- Very fast
- Good for API testing

**Cons:**
- Cannot test browser-rendered UI
- No JavaScript execution
- No visual/DOM testing

## Alternative 4: Mock/Stub Approach

Create a minimal HTTP server that serves the same content.

**Setup:**
```javascript
// mock-server.js
const express = require('express');
const app = express();

app.use(express.static('wled00/data'));
app.listen(8080);
```

**Pros:**
- Simple to set up
- Fast execution
- Works anywhere

**Cons:**
- Not testing actual firmware
- May miss firmware-specific bugs
- Backend logic not tested

## Recommendation

For WLED, the recommended priority is:

1. **Wokwi CLI** (current) - Best balance of accuracy and ease of use
2. **ESP32 QEMU** - If licensing is an issue
3. **Renode** - If QEMU network setup is too complex
4. **Mock approach** - Only for quick UI-only validation

## Migration Guide

If you need to migrate from Wokwi to another solution:

### To ESP32 QEMU:

1. Install QEMU for ESP32
2. Update workflow to build and run QEMU instead of Wokwi
3. Configure network forwarding (may need TAP/TUN devices)
4. Update port mappings in tests

### To Renode:

1. Install Renode in CI
2. Create Renode platform description for your board
3. Write Renode script to start firmware and forward network
4. Update workflow steps

### To Mock Server:

1. Remove firmware build steps
2. Add Node.js HTTP server
3. Serve static files from wled00/data
4. Update baseURL in Playwright config
5. Note: This loses firmware integration testing

## Contributing

If you implement one of these alternatives successfully, please:
1. Document your setup
2. Share your workflow file
3. Update this document with lessons learned
