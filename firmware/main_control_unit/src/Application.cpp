#include <Arduino.h>
#include <driver/i2s.h>
#include <WiFi.h>
#include <WiFiUdp.h>
#include <esp_wifi.h>

#include "Application.h"
#include "I2SMEMSSampler.h"
#include "ADCSampler.h"
#include "I2SOutput.h"
#include "DACOutput.h"
#include "UdpTransport.h"
#include "EspNowTransport.h"
#include "OutputBuffer.h"
#include "config.h"
#include "GenericDevBoardIndicatorLed.h"

// UDP for sending commands
WiFiUDP udp;
const int TARGET_PORT = 4210;

// Debounce timer
unsigned long last_command_time = 0;

static void application_task(void *param) {
  Application *application = reinterpret_cast<Application *>(param);
  application->loop();
}

// Broadcasts "OPEN" to the network
void Application::send_remote_open_command() {
  unsigned long now = millis();
  // Simple 1-second debounce to prevent flooding
  if (now - last_command_time > 1000) {
    Serial.println("Action: SAFETY OVERRIDE - Broadcasting OPEN command...");
    
    // Broadcast to 255.255.255.255
    udp.beginPacket(IPAddress(255, 255, 255, 255), TARGET_PORT);
    udp.print("OPEN");
    udp.endPacket();
    
    last_command_time = now;
    
    // Flash Red rapidly to indicate Override Sent
    for(int i=0; i<3; i++) {
        m_indicator_led->set_is_flashing(true, 0xff0000);
        delay(100);
        m_indicator_led->set_is_flashing(false, 0x000000);
        delay(100);
    }
    m_indicator_led->set_default_color(0x00ff00); // Back to Green
  }
}

// Standard Open Button (Pin 33)
void Application::handle_remote_button() {
  if (digitalRead(REMOTE_OPEN_BUTTON_PIN) == REMOTE_OPEN_BUTTON_ACTIVE_LEVEL) {
    send_remote_open_command();
  }
}

// NEW: Safety Override Button (Pin 32)
void Application::handle_safety_button() {
  if (digitalRead(SAFETY_OVERRIDE_BUTTON_PIN) == SAFETY_OVERRIDE_BUTTON_ACTIVE_LEVEL) {
    Serial.println("!!! SAFETY BUTTON PRESSED !!!");
    send_remote_open_command();
  }
}

Application::Application() {
  m_output_buffer = new OutputBuffer(300 * 16);

#ifdef USE_I2S_MIC_INPUT
  m_input = new I2SMEMSSampler(I2S_NUM_1, i2s_mic_pins, i2s_mic_Config, 128);
#else
  m_input = new ADCSampler(ADC_UNIT_1, ADC1_CHANNEL_7, i2s_adc_config);
#endif

#ifdef USE_I2S_SPEAKER_OUTPUT
  m_output = new I2SOutput(I2S_NUM_0, i2s_speaker_pins);
#else
  m_output = new DACOutput(I2S_NUM_0);
#endif

  m_transport = nullptr;
  m_indicator_led = new GenericDevBoardIndicatorLed();

  if (I2S_SPEAKER_SD_PIN != -1) pinMode(I2S_SPEAKER_SD_PIN, OUTPUT);
}

void Application::begin() {
  m_indicator_led->set_default_color(0);
  m_indicator_led->set_is_flashing(true, 0xff0000);
  m_indicator_led->begin();

  // Setup Buttons
  pinMode(REMOTE_OPEN_BUTTON_PIN, INPUT_PULLUP);     // Pin 33
  pinMode(SAFETY_OVERRIDE_BUTTON_PIN, INPUT_PULLUP); // Pin 32 (New Safety Button)

  // WiFi Connection
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_AP_STA);
  WiFi.begin(WIFI_SSID, WIFI_PSWD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  
  WiFi.setSleep(WIFI_PS_NONE);

  int32_t channel = WiFi.channel();
  
  #ifdef USE_ESP_NOW
    m_transport = new EspNowTransport(m_output_buffer, channel);
  #else
    m_transport = new UdpTransport(m_output_buffer);
  #endif

  m_transport->set_header(TRANSPORT_HEADER_SIZE, transport_header);
  m_transport->begin();

  m_indicator_led->set_default_color(0x00ff00);
  m_indicator_led->set_is_flashing(false, 0x00ff00);
  
  pinMode(GPIO_TRANSMIT_BUTTON, INPUT_PULLDOWN);
  m_output->start(SAMPLE_RATE);
  m_output_buffer->flush();
  
  TaskHandle_t task_handle;
  xTaskCreate(application_task, "application_task", 8192, this, 1, &task_handle);
}

void Application::loop() {
  int16_t *samples = reinterpret_cast<int16_t *>(malloc(sizeof(int16_t) * 128));
  
  while (true) {
    handle_remote_button(); // Check Pin 33
    handle_safety_button(); // Check Pin 32 (Override)

    if (digitalRead(GPIO_TRANSMIT_BUTTON)) {
      m_output->stop();
      m_input->start();
      
      unsigned long start_time = millis();
      while (millis() - start_time < 1000 || digitalRead(GPIO_TRANSMIT_BUTTON)) {
        
        handle_remote_button(); // Allow unlock while talking
        handle_safety_button(); // Allow safety override while talking
        
        int samples_read = m_input->read(samples, 128);
        for (int i = 0; i < samples_read; i++) {
          m_transport->add_sample(samples[i]);
        }
      }
      
      m_transport->flush();
      m_input->stop();
      m_output->start(SAMPLE_RATE);
    }
    
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, HIGH);
    
    unsigned long start_time = millis();
    while (millis() - start_time < 100 || !digitalRead(GPIO_TRANSMIT_BUTTON)) {
      
      handle_remote_button(); 
      handle_safety_button();

      if (digitalRead(GPIO_TRANSMIT_BUTTON)) break;

      m_output_buffer->remove_samples(samples, 128);
      m_output->write(samples, 128);
    }
    
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, LOW);
  }
}