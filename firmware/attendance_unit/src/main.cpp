#include <Arduino.h>
#include <WiFi.h>

// --- CONFIGURATION ---
const char* WIFI_SSID = "Unkown";
const char* WIFI_PASS = "kkkkkkkk"; // <--- DOUBLE CHECK THIS!

// IP Address of the computer running the Python script
const char* SERVER_HOST = "10.42.230.136"; 
const int SERVER_PORT = 65432;

// --- PINS ---
const int BUTTON_PIN = 9;     
const int GREEN_LED = 6;  
const int RED_LED = 7;    

// --- BETTER WIFI CONNECTION LOGIC ---
void connectToWiFi() {
  Serial.println("\n--- Connecting to WiFi ---");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    digitalWrite(RED_LED, !digitalRead(RED_LED)); // Blink while connecting
    
    attempts++;
    
    // If it takes more than 10 seconds (20 attempts), print the status
    if (attempts > 20) {
      Serial.println();
      Serial.print("Still connecting... Status Code: ");
      Serial.println(WiFi.status());
      
      if (WiFi.status() == WL_CONNECT_FAILED) {
        Serial.println("ERROR: Password might be wrong!");
      } else if (WiFi.status() == WL_NO_SSID_AVAIL) {
        Serial.println("ERROR: SSID not found (Check name)");
      }
      
      // Reset attempts to keep the log clean
      attempts = 0;
    }
  }
  
  digitalWrite(RED_LED, LOW);
  Serial.println("\nWiFi Connected!");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
}

void blinkLED(int pin, int times, int speed) {
  for(int i=0; i<times; i++) {
    digitalWrite(pin, HIGH);
    delay(speed);
    digitalWrite(pin, LOW);
    delay(speed);
  }
}

void requestAttendance() {
  if(WiFi.status() != WL_CONNECTED) connectToWiFi();

  WiFiClient client;
  Serial.print("Connecting to Python Server at ");
  Serial.print(SERVER_HOST);
  Serial.println("...");

  if (!client.connect(SERVER_HOST, SERVER_PORT)) {
    Serial.println("Connection Failed! Is Python script running?");
    blinkLED(RED_LED, 3, 100); // Fast red blink = Connection Error
    return;
  }

  // 1. Send Trigger
  client.print("TRIGGER");
  Serial.println("Sent TRIGGER. Waiting for label...");

  // 2. Wait for response (Timeout after 15 seconds)
  String response = "";
  long startTime = millis();
  while (client.connected() && millis() - startTime < 15000) {
    if (client.available()) {
      response = client.readStringUntil('\n'); // Read until newline
      response.trim(); // Remove whitespace
      break; 
    }
  }
  
  client.stop(); // Close connection

  // 3. Process Response
  if (response.length() > 0) {
    Serial.print("Received Label: ");
    Serial.println(response);

    if (response == "Unknown") {
      blinkLED(RED_LED, 5, 200); // Unknown = Red Blinks
    } else {
      blinkLED(GREEN_LED, 3, 500); // Known = Green Blinks
    }
  } else {
    Serial.println("Timeout: No response from Python.");
    blinkLED(RED_LED, 2, 1000);
  }
}

void setup() {
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(GREEN_LED, OUTPUT);
  pinMode(RED_LED, OUTPUT);
  
  digitalWrite(GREEN_LED, LOW);
  digitalWrite(RED_LED, LOW);
  
  connectToWiFi();
}

void loop() {
  if (digitalRead(BUTTON_PIN) == LOW) { // Button Pressed
    delay(50); // Debounce
    if (digitalRead(BUTTON_PIN) == LOW) {
      
      requestAttendance();
      
      // Wait for release
      while(digitalRead(BUTTON_PIN) == LOW) delay(10);
    }
  }
}