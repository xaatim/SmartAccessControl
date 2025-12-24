#pragma once

class Output;
class I2SSampler;
class Transport;
class OutputBuffer;
class IndicatorLed;

class Application
{
private:
  Output *m_output;
  I2SSampler *m_input;
  Transport *m_transport;
  IndicatorLed *m_indicator_led;
  OutputBuffer *m_output_buffer;
  uint32_t m_unlock_until_ms = 0;
  void lock_door();
  void unlock_door_for_ms(uint32_t ms);
  void handle_local_buttons();

public:
  Application();
  void begin();
  void loop();
};
