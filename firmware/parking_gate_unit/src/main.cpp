#include <Arduino.h>
#include <Servo.h>

// --- PIN DEFINITIONS ---
const int TRIG_PIN  = 7;
const int ECHO_PIN  = 6;
const int SERVO_PIN = 9;
const int BUTTON_PIN = 2; 

// --- SETTINGS ---
const int DETECTION_DISTANCE_CM = 50; 
const int GATE_OPEN_ANGLE       = 90; 
const int GATE_CLOSE_ANGLE      = 0;  
const unsigned long GATE_OPEN_MS = 5000;

// --- VARIABLES ---
Servo gateServo;
bool accessAuthorized = false;
bool gateIsOpen = false;
unsigned long gateTimer = 0;
int validReadingsCount = 0; // Counter for stable detection

// --- HELPER FUNCTIONS ---
long getDistance() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  
  long duration = pulseIn(ECHO_PIN, HIGH, 30000); 
  if (duration == 0) return 999; 
  return duration * 0.034 / 2;
}

void openGate() {
  if (!gateIsOpen) {
    gateServo.write(GATE_OPEN_ANGLE);
    gateIsOpen = true;
    gateTimer = millis();
    Serial.println("GATE: OPENING");
  } else {
    gateTimer = millis(); // Extend timer if car is still there
  }
}

void closeGate() {
  gateServo.write(GATE_CLOSE_ANGLE);
  gateIsOpen = false;
  accessAuthorized = false; // Reset Authorization
  validReadingsCount = 0;   // Reset Counter
  Serial.println("GATE: CLOSED");
}

void setup() {
  Serial.begin(9600);
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  
  gateServo.attach(SERVO_PIN);
  gateServo.write(GATE_CLOSE_ANGLE); 
  Serial.println("SYSTEM: READY");
}

void loop() {
  // 1. LISTEN FOR PYTHON
  if (Serial.available() > 0) {
    char cmd = Serial.read();
    if (cmd == 'A') {
      accessAuthorized = true;
      Serial.println("STATUS: AUTHORIZED - WAITING FOR CAR...");
    }
  }

  // 2. READ SENSORS
  long distance = getDistance();
  bool buttonPressed = (digitalRead(BUTTON_PIN) == LOW);

  // --- DEBUGGING: Uncomment this line to see distance in Serial Monitor ---
  // Serial.print("Dist: "); Serial.println(distance);

  // 3. EXIT BUTTON LOGIC (Always works)
  if (buttonPressed) {
    Serial.println("STATUS: BUTTON PRESSED");
    openGate();
    delay(1000); // Debounce
    return;
  }

  // 4. SMART ENTRY LOGIC
  // Only process if we are authorized and gate is closed
  if (accessAuthorized && !gateIsOpen) {
    if (distance > 0 && distance < DETECTION_DISTANCE_CM) {
      validReadingsCount++; // Increment confidence
      
      // Require 10 consecutive detections (~500ms) to confirm it's a car
      if (validReadingsCount > 10) {
        Serial.println("STATUS: CAR CONFIRMED -> OPENING");
        openGate();
        validReadingsCount = 0;
      }
    } else {
      validReadingsCount = 0; // Reset if reading glitches or path clears
    }
  }

  // 5. AUTO CLOSE LOGIC
  if (gateIsOpen && (millis() - gateTimer > GATE_OPEN_MS)) {
    closeGate();
  }

  delay(50); // Loop speed
}