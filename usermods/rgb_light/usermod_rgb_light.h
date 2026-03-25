#pragma once

#include "wled.h"
#include "src/dependencies/json/ArduinoJson-v6.h"

/*
 * RGBLightUsermod – WLEDMM
 *
 * Presents WLED as a generic JSON RGB light over MQTT, compatible with the
 * Home Assistant MQTT Light integration auto-discovery format.
 *
 * Enable by adding -D USERMOD_RGB_LIGHT to your PlatformIO build_flags.
 *
 * MQTT topics:
 *   State : {mqttDeviceTopic}/rgb_light/state
 *   Command: {mqttDeviceTopic}/rgb_light/set
 *   HA discovery (retained): homeassistant/light/<name>/config
 */

class RGBLightUsermod : public Usermod {
  private:
    uint8_t  _lastBri  = 0;
    uint32_t _lastCol  = 0;

    static constexpr uint8_t DEFAULT_ON_BRIGHTNESS = 128;

    // Pack R/G/B into a single uint32 for change detection
    static uint32_t packCol(const byte* c) {
      return ((uint32_t)c[0] << 16) | ((uint32_t)c[1] << 8) | c[2];
    }

    // Build a sanitised device name from mqttDeviceTopic
    // (replace '/' with '_' so it is safe for use in a topic segment)
    void sanitisedName(char* out, size_t len) {
      strncpy(out, mqttDeviceTopic, len - 1);
      out[len - 1] = '\0';
      for (char* p = out; *p; p++) {
        if (*p == '/') *p = '_';
      }
    }

    void publishState() {
      if (!WLED_MQTT_CONNECTED) return;

      char stateTopic[64];
      snprintf_P(stateTopic, sizeof(stateTopic), PSTR("%s/rgb_light/state"), mqttDeviceTopic);

      StaticJsonDocument<256> doc;
      doc[F("state")]      = (bri > 0) ? F("ON") : F("OFF");
      doc[F("brightness")] = bri;
      JsonObject color     = doc.createNestedObject(F("color"));
      color[F("r")]        = colPri[0];
      color[F("g")]        = colPri[1];
      color[F("b")]        = colPri[2];

      char payload[256];
      serializeJson(doc, payload, sizeof(payload));
      mqtt->publish(stateTopic, 0, false, payload);

      _lastBri = bri;
      _lastCol = packCol(colPri);
    }

    void publishDiscovery() {
      if (!WLED_MQTT_CONNECTED) return;

      char devName[64];
      sanitisedName(devName, sizeof(devName));

      char discoveryTopic[96];
      snprintf_P(discoveryTopic, sizeof(discoveryTopic),
                 PSTR("homeassistant/light/%s/config"), devName);

      char stateTopic[64];
      snprintf_P(stateTopic, sizeof(stateTopic),
                 PSTR("%s/rgb_light/state"), mqttDeviceTopic);

      char cmdTopic[64];
      snprintf_P(cmdTopic, sizeof(cmdTopic),
                 PSTR("%s/rgb_light/set"), mqttDeviceTopic);

      char uniqueId[80];
      snprintf_P(uniqueId, sizeof(uniqueId),
                 PSTR("%s_rgb_light"), mqttDeviceTopic);

      StaticJsonDocument<512> doc;
      doc[F("name")]             = F("WLED");
      doc[F("unique_id")]        = uniqueId;
      doc[F("state_topic")]      = stateTopic;
      doc[F("command_topic")]    = cmdTopic;
      doc[F("brightness")]       = true;
      doc[F("rgb")]              = true;
      doc[F("schema")]           = F("json");
      doc[F("brightness_scale")] = 255;

      JsonObject device      = doc.createNestedObject(F("device"));
      JsonArray  identifiers = device.createNestedArray(F("identifiers"));
      identifiers.add(mqttDeviceTopic);
      device[F("name")]         = F("WLED");
      device[F("manufacturer")] = F("WLED-MM");
      device[F("model")]        = F("ESP32");

      char payload[512];
      serializeJson(doc, payload, sizeof(payload));
      mqtt->publish(discoveryTopic, 0, true, payload);  // retained
    }

  public:
    RGBLightUsermod(const char* name, bool enabled)
      : Usermod(name, enabled) {}

    void setup() override {
      initDone = true;
    }

    void loop() override {
      if (!enabled || !initDone) return;
      if (millis() - lastTime < 1000) return;
      lastTime = millis();

      if (!WLED_MQTT_CONNECTED) return;
      if (_lastBri != bri || _lastCol != packCol(colPri)) {
        publishState();
      }
    }

    void onMqttConnect(bool sessionPresent) override {
      if (!enabled) return;

      // Subscribe to the command topic
      char cmdTopic[64];
      snprintf_P(cmdTopic, sizeof(cmdTopic),
                 PSTR("%s/rgb_light/set"), mqttDeviceTopic);
      mqtt->subscribe(cmdTopic, 0);

      // Publish HA discovery payload (retained)
      publishDiscovery();

      // Publish current state
      publishState();
    }

    bool onMqttMessage(char* topic, char* payload) override {
      if (!enabled) return false;

      char cmdTopic[64];
      snprintf_P(cmdTopic, sizeof(cmdTopic),
                 PSTR("%s/rgb_light/set"), mqttDeviceTopic);
      if (strcmp(topic, cmdTopic) != 0) return false;

      StaticJsonDocument<256> doc;
      DeserializationError err = deserializeJson(doc, payload);
      if (err) return true; // handled (but malformed)

      bool stateChanged = false;

      if (doc.containsKey(F("state"))) {
        const char* state = doc[F("state")];
        if (state) {
          uint8_t newBri = (strcmp_P(state, PSTR("ON")) == 0) ? (bri > 0 ? bri : DEFAULT_ON_BRIGHTNESS) : 0;
          if (newBri != bri) {
            bri = newBri;
            stateChanged = true;
          }
        }
      }

      if (doc.containsKey(F("brightness"))) {
        uint8_t b = doc[F("brightness")];
        if (b != bri) {
          bri = b;
          stateChanged = true;
        }
      }

      if (doc.containsKey(F("color"))) {
        JsonObject color = doc[F("color")];
        byte r = color[F("r")] | (byte)0;
        byte g = color[F("g")] | (byte)0;
        byte b = color[F("b")] | (byte)0;
        if (r != colPri[0] || g != colPri[1] || b != colPri[2]) {
          colPri[0] = r;
          colPri[1] = g;
          colPri[2] = b;
          stateChanged = true;
        }
      }

      if (stateChanged) {
        colorUpdated(CALL_MODE_DIRECT_CHANGE);
      }

      return true;
    }

    void onStateChange(uint8_t mode) override {
      if (!initDone || !enabled) return;
      if (WLED_MQTT_CONNECTED) {
        publishState();
      }
    }

    void addToConfig(JsonObject& obj) override {
      Usermod::addToConfig(obj);
    }

    bool readFromConfig(JsonObject& obj) override {
      return Usermod::readFromConfig(obj);
    }

    uint16_t getId() override {
      return USERMOD_ID_RGB_LIGHT;
    }
};
