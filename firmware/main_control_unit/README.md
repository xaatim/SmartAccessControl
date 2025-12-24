# Overview

Main Control Unit firmware for the Smart Access Control intercom (derived from the original ESP32 walkie‑talkie project). It handles receive/playback plus push‑to‑talk capture using ESP‑NOW or UDP broadcast.

Audio is I2S end‑to‑end. Any I2S MEMS mic (e.g. INMP441) and I2S amp (e.g. MAX98357) will work; you can switch to the built‑in ADC/DAC in `config.h` if needed. Pinouts and transport options live in `src/config.h`.

Reference: ESP32 audio deep‑dives https://www.youtube.com/playlist?list=PL5vDt5AALlRfGVUv2x7riDMIOX34udtKD

# Setup

Everything is configured from the `src/config.h` file. To use UDP Broadcast comment out the line:

```
#define USE_ESP_NOW
```

Make sure you update the WiFi SSID and Password:

```
// WiFi credentials
#define WIFI_SSID << YOUR_SSID >>
#define WIFI_PSWD << YOUR_PASSWORD >>
```

The pins for the microphone and the amplifier board are all setup in the same `config.h` file.

# Building and Running

Requires PlatformIO. Open the project, choose the `esp32dev` env (or your board), and build/flash:

```
pio run -e esp32dev
pio run -t upload -e esp32dev
pio device monitor -e esp32dev
```

You need a paired restricted_areas_unit for audio to flow.
