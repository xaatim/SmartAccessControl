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

    void handle_remote_button();     // Check button 33
    void send_remote_open_command(); // Send WiFi signal

public:
    Application();
    void begin();
    void loop();
};