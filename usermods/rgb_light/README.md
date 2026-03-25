# rgb_light Usermod

Presents WLED as a generic JSON RGB light over MQTT, fully compatible with the [Home Assistant MQTT Light](https://www.home-assistant.io/integrations/light.mqtt/) integration auto-discovery format.

## What it does

- On MQTT connect, publishes a retained Home Assistant discovery payload so WLED appears automatically as an RGB light entity in Home Assistant.
- Subscribes to a command topic and handles JSON payloads with `state`, `brightness`, and/or `color` fields.
- Publishes the current WLED state (on/off, brightness, RGB colour) whenever it changes.

## How to enable

Add `-D USERMOD_RGB_LIGHT` to your PlatformIO `build_flags`, for example in `platformio.ini`:

```ini
build_flags =
  ...
  -D USERMOD_RGB_LIGHT
```

## MQTT topics

| Topic | Direction | Description |
|-------|-----------|-------------|
| `{mqttDeviceTopic}/rgb_light/state` | Published by WLED | Current state JSON |
| `{mqttDeviceTopic}/rgb_light/set`   | Subscribed by WLED | Command JSON |
| `homeassistant/light/<name>/config` | Published by WLED (retained) | HA auto-discovery payload |

`{mqttDeviceTopic}` is configured in the WLED MQTT settings (default: `wled/<mac>`).

## State / command payload format

```json
{"state":"ON","brightness":200,"color":{"r":255,"g":128,"b":0}}
```

Command payloads may contain any subset of `state`, `brightness`, and `color`.

## Home Assistant auto-discovery

When MQTT is enabled and the usermod is active, WLED will publish a retained discovery message to `homeassistant/light/<sanitised_device_name>/config`.  Home Assistant (with MQTT discovery enabled) will automatically create a light entity named **WLED** under the device **WLED** (manufacturer: WLED-MM).

## Configuration

The usermod respects the standard WLED enabled/disabled toggle stored in `cfg.json` under the key `RGBLight`.
