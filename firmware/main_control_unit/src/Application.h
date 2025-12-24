#pragma once

#include <Arduino.h>
#include <WiFiUdp.h>

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

    // Helper functions
    void handle_remote_button();  // Pin 33
    void handle_safety_button();  // Pin 32 (New Override)
    void send_remote_open_command();

public:
    Application();
    void begin();
    void loop();
};