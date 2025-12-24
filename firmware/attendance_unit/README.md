# ESP32 Attendance Unit

Minimal PlatformIO firmware for the attendance station. Pressing the button asks the host (Python control unit) to run face recognition; the host replies with the result and the ESP32 drives LEDs accordingly.

## Wiring (ESP32-C3 Super Mini / Tenstar Robot)
- `BUTTON_PIN` (GPIO 9) → momentary button to GND, uses internal pull-up.
- `GREEN_LED_PIN` (GPIO 6) → series resistor → LED → GND.
- `RED_LED_PIN` (GPIO 7) → series resistor → LED → GND.
- Power from USB (5V) with ESP32 3.3V rail powering the LEDs via GPIO.

You can change the pin numbers in `src/main.cpp` if your wiring differs. PlatformIO target board is `esp32-c3-devkitm-1` (works for the Super Mini); if you get an unknown board error, update the Espressif32 platform (`pio pkg update -g -p espressif32`) and retry.

Current `platformio.ini` also sets:
- `monitor_port = COM9` (adjust for your OS)
- `ARDUINO_USB_MODE=1` and `ARDUINO_USB_CDC_ON_BOOT=1` so USB CDC is active at boot on the C3.

## Wi-Fi flow (no serial protocol)
1) Fill `WIFI_SSID`, `WIFI_PASSWORD`, and `HOST_URL` in `src/main.cpp`.
2) On boot, the ESP32 connects to Wi-Fi and prints its IP over Serial (`ATTEND_UNIT_READY_WIFI` + IP).
3) When the button is pressed, the ESP32 sends an HTTP POST to `HOST_URL` with body `{"event":"ATTEND_REQUEST"}`.
4) The host (Python) should process the request, run face recognition, and respond with plain text:
   - `Unknown` → ESP32 blinks red and returns to idle.
   - Any other label text → ESP32 turns green for 3 seconds, then returns to idle.

Example host (Python + Flask):
```python
from flask import Flask, request

app = Flask(__name__)

def run_attendance():
    # TODO: integrate your camera/recognition; return label or "Unknown"
    return "Unknown"

@app.post("/attendance")
def attendance():
    if request.json and request.json.get("event") == "ATTEND_REQUEST":
        label = run_attendance()
        return label, 200
    return "Unknown", 400

app.run(host="0.0.0.0", port=8000)
```

Set `HOST_URL` (e.g., `http://<your-host-ip>:8000/attendance`) to point at that server. If you change the path or port, update `HOST_URL` accordingly.

## Serial protocol (115200 8N1)
- ESP32 sends `ATTEND_REQUEST` once per button press (debounced) and waits for a reply.
- Host replies with one line terminated by `\n`:
  - `RESULT KNOWN <label>` → turn green LED on for a few seconds, print label over Serial.
  - `RESULT UNKNOWN` → blink red LED, then return to idle.
- If no reply arrives within the timeout, the ESP32 blinks red and returns to idle.

## Host integration idea
On the control PC/Raspberry Pi, run the existing attendance handler and bridge Serial:
1. Wait for `ATTEND_REQUEST`.
2. Trigger the camera/recognition pipeline; get label + confidence.
3. Send `RESULT KNOWN <label>` or `RESULT UNKNOWN`.

This keeps the ESP32 simple and lets the Python stack decide everything about recognition.

Example host loop (Python + pyserial):
```python
import serial, time

def run_attendance_once():
    # TODO: trigger your camera + recognition pipeline and return (known, label)
    return False, ""

ser = serial.Serial("/dev/ttyUSB0", 115200, timeout=0.1)

while True:
    line = ser.readline().decode().strip()
    if line == "ATTEND_REQUEST":
        known, label = run_attendance_once()
        if known:
            ser.write(f"RESULT KNOWN {label}\n".encode())
        else:
            ser.write(b"RESULT UNKNOWN\n")
    time.sleep(0.01)
```
