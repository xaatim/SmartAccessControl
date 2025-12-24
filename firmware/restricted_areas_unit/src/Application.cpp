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

// UDP Listener for Python "OPEN" Command
WiFiUDP udpListener;
char packetBuffer[255];

static void application_task(void *param) {
  Application *application = reinterpret_cast<Application *>(param);
  application->loop();
}

void Application::lock_door() {
  pinMode(DOOR_RELAY_PIN, OUTPUT);
  digitalWrite(DOOR_RELAY_PIN, DOOR_RELAY_IDLE_LEVEL);
}

void Application::unlock_door_for_ms(uint32_t ms) {
  Serial.println("Action: Unlock Door");
  digitalWrite(DOOR_RELAY_PIN, DOOR_RELAY_ACTIVE_LEVEL);
  m_unlock_until_ms = millis() + ms;
}

void Application::handle_local_buttons() {
  if (digitalRead(DOOR_EXIT_BUTTON_PIN) == DOOR_EXIT_BUTTON_ACTIVE_LEVEL) {
    unlock_door_for_ms(DOOR_UNLOCK_MS);
  }
  if (m_unlock_until_ms && millis() > m_unlock_until_ms) {
    m_unlock_until_ms = 0;
    lock_door();
  }
}

// Check for Python Command
void Application::handle_wifi_commands() {
  int packetSize = udpListener.parsePacket();
  if (packetSize) {
    int len = udpListener.read(packetBuffer, 255);
    if (len > 0) packetBuffer[len] = 0;
    String command = String(packetBuffer);
    command.trim();
    if (command.equalsIgnoreCase("OPEN")) {
       unlock_door_for_ms(DOOR_UNLOCK_MS);
    }
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

  m_transport = nullptr; // Init in begin()
  m_indicator_led = new GenericDevBoardIndicatorLed();

  if (I2S_SPEAKER_SD_PIN != -1) pinMode(I2S_SPEAKER_SD_PIN, OUTPUT);
}

void Application::begin() {
  m_indicator_led->set_default_color(0);
  m_indicator_led->set_is_flashing(true, 0xff0000);
  m_indicator_led->begin();

  lock_door();
  pinMode(DOOR_EXIT_BUTTON_PIN, INPUT_PULLUP);

  // 1. Connect to WiFi (Required for Python Control)
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_AP_STA); // AP_STA is required for ESP-NOW + WiFi
  WiFi.begin(WIFI_SSID, WIFI_PSWD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // 2. THE FIX: Disable Power Saving to stop Audio Jitter
  WiFi.setSleep(WIFI_PS_NONE);

  // 3. Init ESP-NOW on the Router's Channel
  int32_t channel = WiFi.channel();
  Serial.printf("Setting ESP-NOW to Channel %d\n", channel);
  
  #ifdef USE_ESP_NOW
    m_transport = new EspNowTransport(m_output_buffer, channel);
  #else
    m_transport = new UdpTransport(m_output_buffer);
  #endif

  m_transport->set_header(TRANSPORT_HEADER_SIZE, transport_header);
  m_transport->begin();

  // 4. Start Python Listener (Port 4210)
  udpListener.begin(4210);

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
    handle_local_buttons();
    handle_wifi_commands();

    // Transmit
    if (digitalRead(GPIO_TRANSMIT_BUTTON)) {
      m_output->stop();
      m_input->start();
      unsigned long start_time = millis();
      while (millis() - start_time < 1000 || digitalRead(GPIO_TRANSMIT_BUTTON)) {
        handle_local_buttons();
        handle_wifi_commands();
        int samples_read = m_input->read(samples, 128);
        for (int i = 0; i < samples_read; i++) {
          m_transport->add_sample(samples[i]);
        }
      }
      m_transport->flush();
      m_input->stop();
      m_output->start(SAMPLE_RATE);
    }
    
    // Receive
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, HIGH);
    
    unsigned long start_time = millis();
    while (millis() - start_time < 100 || !digitalRead(GPIO_TRANSMIT_BUTTON)) {
      handle_local_buttons();
      handle_wifi_commands();
      if (digitalRead(GPIO_TRANSMIT_BUTTON)) break;
      m_output_buffer->remove_samples(samples, 128);
      m_output->write(samples, 128);
    }
    
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, LOW);
  }
}