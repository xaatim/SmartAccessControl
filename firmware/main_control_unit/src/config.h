#include <freertos/FreeRTOS.h>
#include <driver/i2s.h>
#include <driver/gpio.h>

// WiFi credentials (not used if ESP-NOW is on, but good to have)
#define WIFI_SSID "Catiiqi_2.4G"
#define WIFI_PSWD "26252423"

// sample rate for the system
#define SAMPLE_RATE 16000

// --- FIX 1: UNCOMMENT THIS so it uses the Digital Mic ---
#define USE_I2S_MIC_INPUT

// I2S Microphone Settings
#define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_LEFT
#define I2S_MIC_SERIAL_CLOCK GPIO_NUM_18
#define I2S_MIC_LEFT_RIGHT_CLOCK GPIO_NUM_19
#define I2S_MIC_SERIAL_DATA GPIO_NUM_21

// Analog Microphone Settings (Unused)
#define ADC_MIC_CHANNEL ADC1_CHANNEL_7

// speaker settings
#define USE_I2S_SPEAKER_OUTPUT

// --- FIX 2: UPDATE SPEAKER PINS (to avoid conflict with Mic) ---
#define I2S_SPEAKER_SERIAL_CLOCK GPIO_NUM_27      // BCLK
#define I2S_SPEAKER_LEFT_RIGHT_CLOCK GPIO_NUM_26  // LRC
#define I2S_SPEAKER_SERIAL_DATA GPIO_NUM_25       // DIN
// Shutdown line (Set to -1 if not connected)
#define I2S_SPEAKER_SD_PIN -1

// transmit button
#define GPIO_TRANSMIT_BUTTON 23

// Which transport do you want to use?
// --- FIX 3: UNCOMMENT THIS for Walkie Talkie mode ---
#define USE_ESP_NOW

// On which wifi channel (1-11) should ESP-Now transmit?
#define ESP_NOW_WIFI_CHANNEL 8

// Header settings
#define TRANSPORT_HEADER_SIZE 3
extern uint8_t transport_header[TRANSPORT_HEADER_SIZE];

// External Declarations (Keep these so config.cpp works)
extern i2s_config_t i2s_adc_config;
extern i2s_config_t i2s_mic_Config;
extern i2s_pin_config_t i2s_mic_pins;
extern i2s_pin_config_t i2s_speaker_pins;