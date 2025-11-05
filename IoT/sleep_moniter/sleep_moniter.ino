// sleep_monitor_fixed.ino
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_ADDR 0x3C
#define OLED_RESET -1

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

const uint8_t LED_PINS[] = {2,3,4,5,6,7,8};
const uint8_t NUM_LEDS = 7;

#define BUFFER_SIZE 3
char buffer[BUFFER_SIZE + 1];
uint8_t idx = 0;
bool inPacket = false;

void setup() {
  for (uint8_t i = 0; i < NUM_LEDS; i++) pinMode(LED_PINS[i], OUTPUT);
  Serial.begin(9600);

  // --- OLED INIT ---
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_ADDR)) {
    Serial.println(F("OLED FAILED! Check wiring or addr 0x3D"));
    while (1);
  }

  showBootScreen();
  setLedLevel(0);
  Serial.println(F("Arduino READY. Send P000 to P100"));
}

void loop() {
  while (Serial.available()) {
    char c = Serial.read();

    // Start of packet
    if (c == 'P') {
      idx = 0;
      inPacket = true;
      Serial.print(F("\n[RX] P"));
      continue;
    }

    // Only accept digits during packet
    if (inPacket && idx < BUFFER_SIZE && isDigit(c)) {
      buffer[idx++] = c;
      Serial.print(c);
    }

    // Packet complete?
    if (inPacket && idx == BUFFER_SIZE) {
      buffer[BUFFER_SIZE] = '\0';
      int pct = atoi(buffer);
      pct = constrain(pct, 0, 100);

      int level = (int)round(pct / 100.0 * NUM_LEDS);
      level = constrain(level, 0, NUM_LEDS);

      setLedLevel(level);
      updateOLED(pct, level);

      Serial.print(F(" → "));
      Serial.print(pct);
      Serial.print(F("% → Level "));
      Serial.println(level);

      inPacket = false;
      idx = 0;

      // Flush any extra junk
      while (Serial.available()) Serial.read();
    }
  }
}

void showBootScreen() {
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);  display.println(F("SLEEP MONITOR"));
  display.setCursor(0,16); display.println(F("Ready..."));
  display.display();
}

void updateOLED(int pct, int lvl) {
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0,0); display.print(F("SLEEP MONITOR"));

  display.setTextSize(3);
  display.setCursor(10,10);
  display.print(pct);
  display.print("%");

  display.setTextSize(1);
  display.setCursor(100, 18); display.print(F("Lvl:"));
  display.setCursor(100, 26); display.print(lvl);
  display.print("/7");
  display.display();
}

void setLedLevel(int lvl) {
  for (uint8_t i = 0; i < NUM_LEDS; i++) {
    digitalWrite(LED_PINS[i], (i < lvl) ? HIGH : LOW);
  }
}