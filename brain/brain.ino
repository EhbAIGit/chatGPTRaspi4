/**
This code controls a NeoPixel strip to simulate the activity of different brain zones. 
It listens for serial commands ('f' for frontal, 't' for temporal, 'p' for parietal) and changes the color of the corresponding LED zone gradually, 
creating a smooth transition effect. 
The loop continuously checks for incoming serial commands and executes the corresponding action based on the received command.
When no command is send for 30 seconds it goes to demo mode.
**/




#include <Adafruit_NeoPixel.h>

// Define the pins for the NeoPixels
#define PIN        D6
#define NUMPIXELS 32

// Define the colors for each brain zone
#define FRONTAL_COLOR pixels.Color(0, 0, 255)
#define TEMPORAL_COLOR pixels.Color(0, 255, 0)
#define PARIETAL_COLOR pixels.Color(255, 0, 0)

Adafruit_NeoPixel pixels(NUMPIXELS, PIN, NEO_GRB + NEO_KHZ800);

// Define the pixel ranges for each brain zone
int frontal[2] = {24, 31};
int temporal[2] = {8, 23};
int parietal[2] = {0, 7};

unsigned long lastCommandTime = 0; // Variable to store the time of the last command
unsigned long demoStartTime = 0;   // Variable to store the start time of the demo mode
const unsigned long demoInterval = 30000; // 30 seconds

void setup() {
  pixels.begin();
  Serial.begin(9600); // Initialize serial communication
  uint32_t newColor = pixels.Color(50, 50, 50);
  setAllPixels(newColor);
}

void setPixelsFade(int pixelPos[2], uint32_t startColor, uint32_t endColor, int transitionTime) {
  int steps = 50;
  int wait = transitionTime / steps;

  for (int i = 0; i <= steps; i++) {
    int r = map(i, 0, steps, (startColor >> 16) & 0xFF, (endColor >> 16) & 0xFF);
    int g = map(i, 0, steps, (startColor >> 8) & 0xFF, (endColor >> 8) & 0xFF);
    int b = map(i, 0, steps, startColor & 0xFF, endColor & 0xFF);

    uint32_t newColor = pixels.Color(r, g, b);

    for (int j = pixelPos[0]; j <= pixelPos[1]; j++) {
      pixels.setPixelColor(j, newColor);
    }

    pixels.show();
    delay(wait);
  }
}

void setAllPixels(uint32_t color) {
  for (int i = 0; i < NUMPIXELS; i++) {
    pixels.setPixelColor(i, color);
  }
  pixels.show();
}


void setOnePixel(int pixelnr, uint32_t color) {
  pixels.setPixelColor(pixelnr, color);
  pixels.show();
}

void loop() {
  unsigned long currentTime = millis(); // Get the current time

  // Check if serial data is available
  if (Serial.available() > 0) {
    lastCommandTime = currentTime; // Update the time of the last command
    char command = Serial.read();
    switch (command) {
      case 'f': // Frontal zone
        setPixelsFade(frontal, pixels.Color(0, 0, 50), pixels.Color(0, 0, 255), 25);
        setPixelsFade(frontal, pixels.Color(0, 0, 255), pixels.Color(0, 0, 50), 25);
        break;
      case 't': // Temporal zone
        setPixelsFade(temporal, pixels.Color(0, 50, 0), pixels.Color(0, 255, 0), 25);
        setPixelsFade(temporal, pixels.Color(0, 255, 0), pixels.Color(0, 50, 0), 25);
        break;
      case 'p': // Parietal zone
        setPixelsFade(parietal, pixels.Color(50, 0, 0), pixels.Color(255, 0, 0), 25);
        setPixelsFade(parietal, pixels.Color(255, 0, 0), pixels.Color(50, 0, 0), 25);
        break;
      case 'a': { // Set all pixels to a specific color
        int r = Serial.parseInt();
        int g = Serial.parseInt();
        int b = Serial.parseInt();
        setAllPixels(pixels.Color(r, g, b));
        break;
      }
      case 'b': { // Set all pixels to a specific color
        int pixelnr = Serial.parseInt();
        int r = Serial.parseInt();
        int g = Serial.parseInt();
        int b = Serial.parseInt();
        setOnePixel(pixelnr,pixels.Color(r, g, b));
        break;
      }
      default:
        // Invalid command
        break;
    }
  }

  // Check if it's time to enter demo mode
  if (currentTime - lastCommandTime >= demoInterval) {
    if (demoStartTime == 0) {
      demoStartTime = currentTime; // Start the demo mode timer
    }

    // Calculate the time elapsed since demo mode started
    unsigned long demoElapsedTime = currentTime - demoStartTime;

    // Determine which brain zone to display based on the elapsed time
    if (demoElapsedTime < 10000) { // 10 seconds for each zone
        setPixelsFade(frontal, pixels.Color(0, 0, 50), pixels.Color(0, 0, 255), 400);
        setPixelsFade(frontal, pixels.Color(0, 0, 255), pixels.Color(0, 0, 50), 400);
    } else if (demoElapsedTime < 20000) {
        setPixelsFade(temporal, pixels.Color(0, 30, 0), pixels.Color(0, 255, 0), 400);
        setPixelsFade(temporal, pixels.Color(0, 255, 0), pixels.Color(0, 30, 0), 400);
    } else {
        setPixelsFade(parietal, pixels.Color(50, 0, 0), pixels.Color(255, 0, 0), 400);
        setPixelsFade(parietal, pixels.Color(255, 0, 0), pixels.Color(50, 0, 0), 400);
      // Reset the demo mode timer when all zones have been displayed
      if (demoElapsedTime >= 30000) {
        demoStartTime = 0;
      }
    }
  }
}
