#pragma once
#include <freertos/FreeRTOS.h>
#include <driver/i2s.h>
#include <driver/gpio.h>

// --- WIFI CREDENTIALS ---
#define WIFI_SSID "Catiiqi_2.4G"
#define WIFI_PSWD "26252423"

#define SAMPLE_RATE 16000

// --- BUTTONS ---
// 1. Standard Remote Open (Pin 33)
#define REMOTE_OPEN_BUTTON_PIN GPIO_NUM_33
#define REMOTE_OPEN_BUTTON_ACTIVE_LEVEL LOW 

// 2. Safety Override Button (Pin 32) - NEW
#define SAFETY_OVERRIDE_BUTTON_PIN GPIO_NUM_32
#define SAFETY_OVERRIDE_BUTTON_ACTIVE_LEVEL LOW 

// --- AUDIO SETTINGS ---
#define USE_I2S_MIC_INPUT
#define USE_I2S_SPEAKER_OUTPUT

// --- MIC PINS ---
#define I2S_MIC_CHANNEL I2S_CHANNEL_FMT_ONLY_LEFT
#define I2S_MIC_SERIAL_CLOCK GPIO_NUM_18
#define I2S_MIC_LEFT_RIGHT_CLOCK GPIO_NUM_19
#define I2S_MIC_SERIAL_DATA GPIO_NUM_21

// --- SPEAKER PINS ---
#define I2S_SPEAKER_SERIAL_CLOCK GPIO_NUM_27
#define I2S_SPEAKER_LEFT_RIGHT_CLOCK GPIO_NUM_26
#define I2S_SPEAKER_SERIAL_DATA GPIO_NUM_25
#define I2S_SPEAKER_SD_PIN -1

// Push-to-Talk Button (Pin 23)
#define GPIO_TRANSMIT_BUTTON 23

// --- TRANSPORT ---
#define USE_ESP_NOW

#define TRANSPORT_HEADER_SIZE 3
extern uint8_t transport_header[TRANSPORT_HEADER_SIZE];

extern i2s_config_t i2s_adc_config;
extern i2s_config_t i2s_mic_Config;
extern i2s_pin_config_t i2s_mic_pins;
extern i2s_pin_config_t i2s_speaker_pins;