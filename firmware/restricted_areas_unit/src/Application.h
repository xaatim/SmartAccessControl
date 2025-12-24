#pragma once

#include <Arduino.h>
#include <WiFiUdp.h> // Required for UDP

class I2SSampler;
class I2SOutput;
class Transport;
class OutputBuffer;
class IndicatorLed;

class Application
{
private:
    I2SSampler *m_input;
    I2SOutput *m_output;
    Transport *m_transport;
    OutputBuffer *m_output_buffer;
    IndicatorLed *m_indicator_led;

    uint32_t m_unlock_until_ms = 0;

    void handle_local_buttons();
    void handle_wifi_commands(); // <--- LISTENS FOR PYTHON COMMAND

public:
    Application();
    void begin();
    void loop();
    void lock_door();
    void unlock_door_for_ms(uint32_t ms);
};