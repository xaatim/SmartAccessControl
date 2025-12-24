# Overview

Restricted Areas Unit firmware for the Smart Access Control intercom (copy of main_control_unit with door control added). Handles receive/playback plus push‑to‑talk capture via ESP‑NOW/UDP, and can drive a 12V solenoid through a 5V relay with local/remote unlock.

Audio is I2S end‑to‑end (INMP441 mic on GPIO 18/19/21; MAX98357 amp on GPIO 27/26/25). Door control wiring and options live in `src/config.h`.

# Door control wiring (defaults)
- Relay IN: GPIO 32 (active LOW by default)  
- Exit button: GPIO 33 (to GND, internal pull-up)  
- Override (hazard) lives on the main control unit and triggers this unit remotely (no local override button here)  
- Unlock pulse: `DOOR_UNLOCK_MS` (default 3000 ms)
- Remote unlock: simple TCP server on `DOOR_TCP_PORT` (default 65433) accepts line `OPEN`

# Setup
- Transport: leave `USE_ESP_NOW` on for intercom; comment it to use UDP broadcast.
- WiFi: set `WIFI_SSID`/`WIFI_PSWD` if you want remote unlock via TCP. ESP‑NOW channel must match the AP channel when both are enabled.
- Door: adjust relay/button pins/active levels in `src/config.h` for your hardware.

# Building and Running

Requires PlatformIO. Build/flash the `esp32dev` env (or your board):

```
pio run -e esp32dev
pio run -t upload -e esp32dev
pio device monitor -e esp32dev
```

Remote unlock example (Python):
```python
import socket
with socket.create_connection(("device_ip", 65433), timeout=2) as s:
    s.sendall(b\"OPEN\\n\")
    print(s.recv(16))
```
