#include <Arduino.h>       
#include <WiFi.h>          
#include <WiFiClient.h>
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

// --- DOOR CONTROL CONFIG ---
const char* DOOR_SERVER_HOST = "192.168.0.138"; 
const int DOOR_SERVER_PORT = 65433; 

// ⚠️ UPDATED PINS (AVOIDING I2S & INPUT-ONLY PINS) ⚠️
const int RELAY_PIN = 32;       // <--- GPIO 32 (Standard Output)
const int EXIT_BUTTON_PIN = 33; // <--- GPIO 33 (Standard IO with Pullup)

// --- LOGIC (Active HIGH) ---
// HIGH = 3.3V -> Solenoid Contracts (ON)
// LOW  = 0V   -> Solenoid Releases (OFF)
const int RELAY_ON = LOW;      
const int RELAY_OFF = HIGH;      

WiFiClient doorClient;

static void application_task(void *param) {
  Application *application = reinterpret_cast<Application *>(param);
  application->loop();
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

#ifdef USE_ESP_NOW
  m_transport = new EspNowTransport(m_output_buffer, ESP_NOW_WIFI_CHANNEL);
#else
  m_transport = new UdpTransport(m_output_buffer);
#endif

  m_transport->set_header(TRANSPORT_HEADER_SIZE, transport_header);
  m_indicator_led = new GenericDevBoardIndicatorLed();

  if (I2S_SPEAKER_SD_PIN != -1) {
    pinMode(I2S_SPEAKER_SD_PIN, OUTPUT);
  }
}

void unlockDoorRemote() {
  Serial.println(">>> REMOTE OPEN COMMAND <<<");
  digitalWrite(RELAY_PIN, RELAY_ON); 
  delay(3000); 
  digitalWrite(RELAY_PIN, RELAY_OFF); 
  Serial.println(">>> DOOR CLOSED <<<");
}

void Application::begin() {
  // 1. FORCE RELAY OFF IMMEDIATELY
  pinMode(RELAY_PIN, OUTPUT);
  digitalWrite(RELAY_PIN, RELAY_OFF); // Sets Pin 32 to 0V (Lock released)

  m_indicator_led->set_default_color(0);
  m_indicator_led->set_is_flashing(true, 0xff0000);
  m_indicator_led->begin();

  pinMode(EXIT_BUTTON_PIN, INPUT_PULLUP);

  // 2. Setup WiFi
  Serial.print("My IDF Version is: ");
  Serial.println(esp_get_idf_version());

  WiFi.mode(WIFI_STA);
#ifndef USE_ESP_NOW
  WiFi.begin(WIFI_SSID, WIFI_PSWD);
  if (WiFi.waitForConnectResult() != WL_CONNECTED) {
    Serial.println("Connection Failed! Rebooting...");
    delay(5000);
    ESP.restart();
  }
  WiFi.setSleep(WIFI_PS_NONE);
  Serial.print("My IP Address is: ");
  Serial.println(WiFi.localIP());
#else
  WiFi.disconnect();
#endif
  
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
    
    // --- PART 1: DOOR LOGIC ---
    
    // A. Manual Exit Button (Momentary)
    if (digitalRead(EXIT_BUTTON_PIN) == LOW) {
        digitalWrite(RELAY_PIN, RELAY_ON);  // Button Pressed -> Power ON
    } else {
        digitalWrite(RELAY_PIN, RELAY_OFF); // Button Released -> Power OFF
    }

    // B. Maintain Connection to Python Server
    if (WiFi.status() == WL_CONNECTED) {
        if (!doorClient.connected()) {
            static unsigned long lastTry = 0;
            if (millis() - lastTry > 5000) {
                lastTry = millis();
                doorClient.connect(DOOR_SERVER_HOST, DOOR_SERVER_PORT);
                if(doorClient.connected()) doorClient.print("INTERCOM_UNIT_READY");
            }
        }
        
        // C. Read Commands
        if (doorClient.connected() && doorClient.available()) {
            String msg = doorClient.readStringUntil('\n');
            msg.trim();
            if (msg == "OPEN") {
                unlockDoorRemote(); 
            }
        }
    }

    // --- PART 2: AUDIO ---
    if (digitalRead(GPIO_TRANSMIT_BUTTON)) {
      digitalWrite(RELAY_PIN, RELAY_OFF); // Safety release

      Serial.println("Started transmitting");
      m_indicator_led->set_is_flashing(true, 0xff0000);
      
      m_output->stop();
      m_input->start();
      
      unsigned long start_time = millis();
      while (millis() - start_time < 1000 || digitalRead(GPIO_TRANSMIT_BUTTON)) {
        int samples_read = m_input->read(samples, 128);
        for (int i = 0; i < samples_read; i++) {
          m_transport->add_sample(samples[i]);
        }
      }
      m_transport->flush();
      Serial.println("Finished transmitting");
      m_indicator_led->set_is_flashing(false, 0xff0000);
      m_input->stop();
      m_output->start(SAMPLE_RATE);
    }
    
    // Receive Audio
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, HIGH);
    
    unsigned long receive_start = millis();
    while (millis() - receive_start < 100 || !digitalRead(GPIO_TRANSMIT_BUTTON)) {
      m_output_buffer->remove_samples(samples, 128);
      m_output->write(samples, 128);
      if (millis() - receive_start > 50) break; 
    }
    if (I2S_SPEAKER_SD_PIN != -1) digitalWrite(I2S_SPEAKER_SD_PIN, LOW);
  }
}