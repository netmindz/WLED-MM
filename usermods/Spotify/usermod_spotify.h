#pragma once

#include "wled.h"

#include <SpotifyArduino.h>
#include <SpotifyArduinoCert.h>

#include <WiFiClientSecure.h>


/*
Fetch now playing data from Spotify
*/
WiFiClientSecure client;
SpotifyArduino spotify(client, "", "", "");

void printCurrentlyPlayingToSerial(CurrentlyPlaying currentlyPlaying)
{
    // Use the details in this method or if you want to store them
    // make sure you copy them (using something like strncpy)
    // const char* artist =

    USER_PRINTLN("--------- Currently Playing ---------");

    USER_PRINT("Is Playing: ");
    if (currentlyPlaying.isPlaying)
    {
        USER_PRINTLN("Yes");
    }
    else
    {
        USER_PRINTLN("No");
    }

    USER_PRINT("Track: ");
    USER_PRINTLN(currentlyPlaying.trackName);
    USER_PRINT("Track URI: ");
    USER_PRINTLN(currentlyPlaying.trackUri);
    USER_PRINTLN();

    USER_PRINTLN("Artists: ");
    for (int i = 0; i < currentlyPlaying.numArtists; i++)
    {
        USER_PRINT("Name: ");
        USER_PRINTLN(currentlyPlaying.artists[i].artistName);
        USER_PRINT("Artist URI: ");
        USER_PRINTLN(currentlyPlaying.artists[i].artistUri);
        USER_PRINTLN();
    }

    USER_PRINT("Album: ");
    USER_PRINTLN(currentlyPlaying.albumName);
    USER_PRINT("Album URI: ");
    USER_PRINTLN(currentlyPlaying.albumUri);
    USER_PRINTLN();

    if (currentlyPlaying.contextUri != NULL)
    {
        USER_PRINT("Context URI: ");
        USER_PRINTLN(currentlyPlaying.contextUri);
        USER_PRINTLN();
    }

    long progress = currentlyPlaying.progressMs; // duration passed in the song
    long duration = currentlyPlaying.durationMs; // Length of Song
    USER_PRINT("Elapsed time of song (ms): ");
    USER_PRINT(progress);
    USER_PRINT(" of ");
    USER_PRINTLN(duration);
    USER_PRINTLN();

    float percentage = ((float)progress / (float)duration) * 100;
    int clampedPercentage = (int)percentage;
    USER_PRINT("<");
    for (int j = 0; j < 50; j++)
    {
        if (clampedPercentage >= (j * 2))
        {
            USER_PRINT("=");
        }
        else
        {
            USER_PRINT("-");
        }
    }
    USER_PRINTLN(">");
    USER_PRINTLN();

    // will be in order of widest to narrowest
    // currentlyPlaying.numImages is the number of images that
    // are stored
    for (int i = 0; i < currentlyPlaying.numImages; i++)
    {
        USER_PRINTLN("------------------------");
        USER_PRINT("Album Image: ");
        USER_PRINTLN(currentlyPlaying.albumImages[i].url);
        USER_PRINT("Dimensions: ");
        USER_PRINT(currentlyPlaying.albumImages[i].width);
        USER_PRINT(" x ");
        USER_PRINT(currentlyPlaying.albumImages[i].height);
        USER_PRINTLN();
    }
    USER_PRINTLN("------------------------");
}

class SpotifyUsermod : public Usermod {

  private:

    // Private class members. You can declare variables and functions only accessible to your usermod here

    String clientId = "";
    String clientSecret = "";
    String refreshToken = "";


    // any private methods should go here (non-inline method should be defined out of class)
    void publishMqtt(const char* state, bool retain = false); // example for publishing MQTT message

    const char *loginLinkTemplate = "<a href=\"https://accounts.spotify.com/authorize?client_id=%s&response_type=code&redirect_uri=%s&scope=%s\">Login</a>";
    const char *scope = "user-read-playback-state";


    unsigned long delayBetweenRequests = 10000; // Time between requests (1 minute)
    unsigned long requestDueTime = 0;           //time when request due


  public:

    SpotifyUsermod(bool enabled):Usermod("Spotify", enabled) {} //WLEDMM

    
    // methods called by WLED (can be inlined as they are called only once but if you call them explicitly define them out of class)

    /*
     * setup() is called once at boot. WiFi is not yet connected at this point.
     * readFromConfig() is called prior to setup()
     * You can use it to initialize variables, sensors or similar.
     */
    void setup() {
      spotify.setRefreshToken(refreshToken.c_str());
      initDone = true;
    }


    /*
     * connected() is called every time the WiFi is (re)connected
     * Use it to initialize network interfaces
     */
    void connected() {
      if (!enabled) return;
      USER_PRINTLN("Connected to WiFi!");
      client.setCACert(spotify_server_cert);
      initDone = true;
      const char *refreshToken = NULL;
      String callbackURI = "http://" +  WiFi.localIP().toString() + "/settings/um?um=Spotify";
      if(false) {
      // if(strcmp(refreshToken.c_str(), "") == 0) {
        USER_PRINTLN("Fetch refresh token");
        refreshToken = spotify.requestAccessTokens("AQBhcQ4OCmawSPENF8ZWizBRjE9vawQvrOnpsZzzOy3NdsK37WrqyZSSBRK2toNCABH1AIPcXZSVK3H-ya77wS_bEcd85nX1XDYPFVKEEzIzy4klRqfg8RtCyR14a2xTY1ya7I_mmpJBvOb9ZEL0tfT97QNQu3_K8-XaBAPMxEfkAMyJYE_HTVn37I6Q5FIFDL5MmHHZvj3nV7C_u9aqd9dWASGLyv3tWhwi", callbackURI.c_str());
        spotify.setRefreshToken(refreshToken);
      }

      USER_PRINTLN("Refreshing Access Tokens");
      if (!spotify.refreshAccessToken())      {
          USER_PRINTLN("Failed to get access tokens");
      }
      USER_PRINTLN("SpotifyUsermod::connected completed");
    }


    /*
     * loop() is called continuously. Here you can check for events, read sensors, etc.
     */
    void loop() {
      // if usermod is disabled or called during strip updating just exit
      // NOTE: on very long strips strip.isUpdating() may always return true so update accordingly
      if (!enabled || strip.isUpdating()) return;

      // do your magic here
      if (millis() - lastTime > 1000) {
        // USER_PRINTLN("I'm alive!");
        lastTime = millis();
        if (millis() > requestDueTime)
        {
          USER_PRINT("Free Heap: ");
          USER_PRINTLN(ESP.getFreeHeap());

          USER_PRINTLN("getting currently playing song:");
          // Market can be excluded if you want e.g. spotify.getCurrentlyPlaying()
          int status = spotify.getCurrentlyPlaying(printCurrentlyPlayingToSerial, "GB");
          if (status == 200){
              USER_PRINTLN("Successfully got currently playing");
          }
          else if (status == 204) {
              USER_PRINTLN("Doesn't seem to be anything playing");
          }
          else {
              USER_PRINT("Error: ");
              USER_PRINTLN(status);
          }
          requestDueTime = millis() + delayBetweenRequests;
        }
      }
    }


    /*
     * addToJsonInfo() can be used to add custom entries to the /json/info part of the JSON API.
     * Creating an "u" object allows you to add custom key/value pairs to the Info section of the WLED web UI.
     * Below it is shown how this could be used for e.g. a light sensor
     */
    void addToJsonInfo(JsonObject& root)
    {
      // if "u" object does not exist yet wee need to create it
      JsonObject user = root["u"];
      if (user.isNull()) user = root.createNestedObject("u");

      //this code adds "u":{"ExampleUsermod":[20," lux"]} to the info object
      //int reading = 20;
      //JsonArray lightArr = user.createNestedArray(FPSTR(_name))); //name
      //lightArr.add(reading); //value
      //lightArr.add(F(" lux")); //unit

      // if you are implementing a sensor usermod, you may publish sensor data
      //JsonObject sensor = root[F("sensor")];
      //if (sensor.isNull()) sensor = root.createNestedObject(F("sensor"));
      //temp = sensor.createNestedArray(F("light"));
      //temp.add(reading);
      //temp.add(F("lux"));
    }


    /*
     * addToJsonState() can be used to add custom entries to the /json/state part of the JSON API (state object).
     * Values in the state object may be modified by connected clients
     */
    void addToJsonState(JsonObject& root)
    {
      if (!initDone || !enabled) return;  // prevent crash on boot applyPreset()

      JsonObject usermod = root[FPSTR(_name)];
      if (usermod.isNull()) usermod = root.createNestedObject(FPSTR(_name));

      usermod["refreshToken"] = refreshToken;
    }


    /*
     * readFromJsonState() can be used to receive data clients send to the /json/state part of the JSON API (state object).
     * Values in the state object may be modified by connected clients
     */
    void readFromJsonState(JsonObject& root)
    {
      if (!initDone) return;  // prevent crash on boot applyPreset()

      JsonObject usermod = root[FPSTR(_name)];
      if (!usermod.isNull()) {
        // expect JSON usermod data in usermod name object: {"ExampleUsermod:{"user0":10}"}
        refreshToken = usermod["refreshToken"] | refreshToken; //if "refreshToken" key exists in JSON, update, else keep old value
      }
      // you can as well check WLED state JSON keys
      //if (root["bri"] == 255) Serial.println(F("Don't burn down your garage!"));
    }


    /*
     * addToConfig() can be used to add custom persistent settings to the cfg.json file in the "um" (usermod) object.
     * It will be called by WLED when settings are actually saved (for example, LED settings are saved)
     * If you want to force saving the current state, use serializeConfig() in your loop().
     * 
     * CAUTION: serializeConfig() will initiate a filesystem write operation.
     * It might cause the LEDs to stutter and will cause flash wear if called too often.
     * Use it sparingly and always in the loop, never in network callbacks!
     * 
     * addToConfig() will make your settings editable through the Usermod Settings page automatically.
     *
     */
    void addToConfig(JsonObject& root)
    {
      Usermod::addToConfig(root); JsonObject top = root[FPSTR(_name)]; //WLEDMM
      top["refreshToken"] = refreshToken;
      top["code"] = "example3";
    }


    /*
     * readFromConfig() can be used to read back the custom settings you added with addToConfig().
     * This is called by WLED when settings are loaded (currently this only happens immediately after boot, or after saving on the Usermod Settings page)
     * 
     * readFromConfig() is called BEFORE setup(). This means you can use your persistent values in setup() (e.g. pin assignments, buffer sizes),
     * but also that if you want to write persistent values to a dynamic buffer, you'd need to allocate it here instead of in setup.
     * If you don't know what that is, don't fret. It most likely doesn't affect your use case :)
     * 
     * Return true in case the config values returned from Usermod Settings were complete, or false if you'd like WLED to save your defaults to disk (so any missing values are editable in Usermod Settings)
     * 
     * getJsonValue() returns false if the value is missing, or copies the value into the variable provided and returns true if the value is present
     * The configComplete variable is true only if the "exampleUsermod" object and all values are present.  If any values are missing, WLED will know to call addToConfig() to save them
     * 
     * This function is guaranteed to be called on boot, but could also be called every time settings are updated
     */
    bool readFromConfig(JsonObject& root)
    {
      // default settings values could be set here (or below using the 3-argument getJsonValue()) instead of in the class definition or constructor
      // setting them inside readFromConfig() is slightly more robust, handling the rare but plausible use case of single value being missing after boot (e.g. if the cfg.json was manually edited and a value was removed)

      bool configComplete = Usermod::readFromConfig(root);JsonObject top = root[FPSTR(_name)]; //WLEDMM

      configComplete &= getJsonValue(top["refreshToken"], refreshToken);

      return configComplete;
    }


    /*
     * appendConfigData() is called when user enters usermod settings page
     * it may add additional metadata for certain entry fields (adding drop down is possible)
     * be careful not to add too much as oappend() buffer is limited to 3k
     */
    void appendConfigData()
    {
      char populatedLoginLink[800];
      String callbackURI = "http://" +  WiFi.localIP().toString() + "/settings/um?um=Spotify";
      sprintf(populatedLoginLink, loginLinkTemplate, clientId.c_str(), callbackURI.c_str(), scope);
      oappend(SET_F("addInfo('")); oappend(String(FPSTR(_name)).c_str()); oappend(SET_F(":refreshToken")); oappend(SET_F("',1,'")); oappend(populatedLoginLink);oappend("');");
    }
  

#ifndef WLED_DISABLE_MQTT
    /**
     * handling of MQTT message
     * topic only contains stripped topic (part after /wled/MAC)
     */
    bool onMqttMessage(char* topic, char* payload) {
      // check if we received a command
      //if (strlen(topic) == 8 && strncmp_P(topic, PSTR("/command"), 8) == 0) {
      //  String action = payload;
      //  if (action == "on") {
      //    enabled = true;
      //    return true;
      //  } else if (action == "off") {
      //    enabled = false;
      //    return true;
      //  } else if (action == "toggle") {
      //    enabled = !enabled;
      //    return true;
      //  }
      //}
      return false;
    }

    /**
     * onMqttConnect() is called when MQTT connection is established
     */
    void onMqttConnect(bool sessionPresent) {
      // do any MQTT related initialisation here
      //publishMqtt("I am alive!");
    }
#endif

    /*
     * getId() allows you to optionally give your V2 usermod an unique ID (please define it in const.h!).
     * This could be used in the future for the system to determine whether your usermod is installed.
     */
    uint16_t getId()
    {
      return USERMOD_ID_SPOTIFY;
    }

   //More methods can be added in the future, this example will then be extended.
   //Your usermod will remain compatible as it does not need to implement all methods from the Usermod base class!
};


// add more strings here to reduce flash memory usage


// implementation of non-inline member methods

void SpotifyUsermod::publishMqtt(const char* state, bool retain)
{
#ifndef WLED_DISABLE_MQTT
  //Check if MQTT Connected, otherwise it will crash the 8266
  if (WLED_MQTT_CONNECTED) {
    char subuf[64];
    strcpy(subuf, mqttDeviceTopic);
    strcat_P(subuf, PSTR("/example"));
    mqtt->publish(subuf, 0, retain, state);
  }
#endif
}
