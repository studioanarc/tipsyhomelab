# Sensor Guide

Complete guide to all supported sensors, including wiring diagrams, calibration procedures, and MQTT topic structures.

---

## Table of Contents

1. [Sensor Overview](#sensor-overview)
2. [Bubble Counters](#bubble-counters)
3. [Hydrometers](#hydrometers)
4. [Temperature Sensors](#temperature-sensors)
5. [pH Sensors](#ph-sensors)
6. [Pressure Sensors](#pressure-sensors)
7. [MQTT Topics](#mqtt-topics)
8. [Calibration](#calibration)
9. [Troubleshooting](#troubleshooting)

---

## Sensor Overview

### Minimum Requirements

For basic fermentation monitoring:
- **1x Bubble Counter** OR **1x Hydrometer**
- **1x Temperature Sensor** (highly recommended)

For Pet Nat production:
- **1x Bubble Counter** (for timing)
- **1x Hydrometer** (for gravity)
- **1x Temperature Sensor** (for compensation)

### Sensor Comparison

| Sensor | Cost | Accuracy | Install | Power | Lifespan | Best For |
|--------|------|----------|---------|-------|----------|----------|
| Bubble Counter (Optical) | $ | Medium | Easy | Low | Years | Activity tracking |
| Bubble Counter (Acoustic) | $ | Medium | Easy | Very Low | Years | Activity tracking |
| iSpindel | $$$ | High | Medium | 4-8 weeks | 1-2 years | Professional monitoring |
| Tilt | $$$$ | High | Easy | 6-12 months | 2-3 years | Ease of use |
| DS18B20 Temp | $ | High | Easy | Low | Years | Temperature |
| Thermowell + DS18B20 | $$ | Very High | Medium | Low | Years | Accurate temp |
| Atlas pH | $$$$ | Very High | Hard | Medium | 1-2 years | Research |
| Pressure Transducer | $$$ | High | Hard | Medium | Years | Pet Nat safety |

---

## Bubble Counters

Track fermentation activity by counting CO2 bubbles through an airlock.

### Types

#### 1. Optical (IR) Bubble Counter

Uses infrared LED and photodiode to detect bubbles optically.

**Pros:**
- No contact with fermentation
- Very reliable
- Easy to build
- Low cost ($5-10)

**Cons:**
- Requires transparent airlock
- Sensitive to ambient light
- Requires consistent placement

**Hardware:**
```
Required Components:
- ESP8266 or ESP32 ($3-8)
- IR LED 940nm ($0.50)
- IR Photodiode ($0.50)
- 220Ω resistor (for LED)
- 10kΩ resistor (for photodiode)
- S-shaped airlock (transparent)
- Micro USB cable + power adapter
```

**Wiring Diagram:**
```
                         ESP8266/ESP32
                    ┌─────────────────────┐
                    │                     │
    IR LED          │  D1 (GPIO5)    3.3V │
      ├─────────────┤                     │
      │             │                     │
    [220Ω]          │                     │
      │             │                     │
    ──┴──           │                     │
     ───  (cathode) │                     │
                    │                     │
                    │                     │
  Photodiode        │  D2 (GPIO4)     GND │
      ├─────────────┤                     │
      │             │                     │
    [10kΩ]          │                     │
      │             │                     │
    ──┴─── GND      │                     │
                    │                     │
                    └─────────────────────┘

Physical Setup:
    ┌─────────┐
    │ Airlock │
    │    ║    │  ← Bubble passes here
    │  ╔═╬═╗  │
    │  ║ ║ ║  │
    └──╨─╨─╨──┘
       │   │
    [LED] [Photo]  ← Mount on opposite sides
       ↓   ↑
    IR beam broken by bubble
```

**ESP8266 Code:**
```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi settings
const char* ssid = "YourWiFi";
const char* password = "YourWiFiPassword";

// MQTT settings
const char* mqtt_server = "192.168.1.100";
const int mqtt_port = 1883;
const char* mqtt_user = "tipsylab";
const char* mqtt_pass = "YourMQTTPassword";
const char* mqtt_topic = "tipsylab/batch1/bubbles";
const char* mqtt_client_id = "bubble_counter_1";

// Hardware pins
const int IR_LED_PIN = D1;      // GPIO5
const int PHOTO_PIN = D2;        // GPIO4

// Bubble detection
const int THRESHOLD = 512;       // Analog threshold (0-1023)
const int DEBOUNCE_MS = 100;     // Minimum time between bubbles
unsigned long lastBubbleTime = 0;
unsigned long totalBubbles = 0;
bool lastState = false;

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  pinMode(IR_LED_PIN, OUTPUT);
  digitalWrite(IR_LED_PIN, HIGH);  // IR LED always on

  setupWiFi();
  client.setServer(mqtt_server, mqtt_port);

  Serial.println("Bubble Counter Ready");
}

void setupWiFi() {
  delay(10);
  Serial.print("Connecting to WiFi...");
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println(" Connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Connecting to MQTT...");

    if (client.connect(mqtt_client_id, mqtt_user, mqtt_pass)) {
      Serial.println(" Connected!");
    } else {
      Serial.print(" Failed, rc=");
      Serial.print(client.state());
      Serial.println(" Retrying in 5s");
      delay(5000);
    }
  }
}

void publishBubble() {
  StaticJsonDocument<200> doc;
  doc["count"] = totalBubbles;
  doc["timestamp"] = millis();
  doc["interval"] = millis() - lastBubbleTime;

  char buffer[200];
  serializeJson(doc, buffer);

  client.publish(mqtt_topic, buffer, true);  // Retained message

  Serial.print("Bubble #");
  Serial.print(totalBubbles);
  Serial.print(" - Interval: ");
  Serial.print(millis() - lastBubbleTime);
  Serial.println("ms");
}

void loop() {
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();

  // Read photodiode
  int reading = analogRead(PHOTO_PIN);
  bool currentState = (reading < THRESHOLD);  // Bubble blocks IR

  // Detect rising edge (bubble passing)
  if (currentState && !lastState) {
    unsigned long now = millis();

    // Debounce
    if (now - lastBubbleTime > DEBOUNCE_MS) {
      totalBubbles++;
      publishBubble();
      lastBubbleTime = now;
    }
  }

  lastState = currentState;
  delay(10);
}
```

**Calibration:**
1. Place sensor on airlock
2. Monitor serial output
3. Adjust `THRESHOLD` value:
   - Too low: Misses bubbles
   - Too high: False positives
4. Typical range: 400-700
5. Test by blowing through airlock

#### 2. Acoustic Bubble Counter

Uses microphone to detect bubble "pop" sound.

**Pros:**
- Works with opaque airlocks
- No alignment needed
- Very low power

**Cons:**
- Sensitive to ambient noise
- Requires DSP filtering
- More complex code

**Hardware:**
```
- ESP32 (required for better ADC)
- MAX9814 microphone module
- 3D-printed mounting clip
```

**Wiring:**
```
MAX9814          ESP32
--------         -----
VDD       ───→   3.3V
GND       ───→   GND
OUT       ───→   GPIO34 (ADC1_CH6)
AR        ───→   (leave floating for auto-gain)
```

**Code** (simplified):
```cpp
// Detect bubble pop using FFT
#include "arduinoFFT.h"

const int SAMPLE_RATE = 8000;
const int SAMPLES = 128;
const int POP_FREQ_MIN = 1000;  // Hz
const int POP_FREQ_MAX = 4000;  // Hz

double vReal[SAMPLES];
double vImag[SAMPLES];
arduinoFFT FFT = arduinoFFT(vReal, vImag, SAMPLES, SAMPLE_RATE);

void detectBubble() {
  // Sample audio
  for (int i = 0; i < SAMPLES; i++) {
    vReal[i] = analogRead(34);
    vImag[i] = 0;
    delayMicroseconds(1000000 / SAMPLE_RATE);
  }

  // Perform FFT
  FFT.Windowing(FFT_WIN_TYP_HAMMING, FFT_FORWARD);
  FFT.Compute(FFT_FORWARD);
  FFT.ComplexToMagnitude();

  // Check for pop frequency
  double peak = FFT.MajorPeak();
  if (peak > POP_FREQ_MIN && peak < POP_FREQ_MAX) {
    // Detected bubble pop!
    totalBubbles++;
    publishBubble();
  }
}
```

---

## Hydrometers

Measure specific gravity to track fermentation progress.

### iSpindel

**Description**: DIY floating hydrometer with WiFi connectivity.

**Features:**
- Specific gravity measurement
- Temperature sensor
- Battery powered (4-8 weeks)
- WiFi direct or via MQTT
- Sleep mode for power saving

**Hardware:**
```
Required Parts ($60-80):
- Wemos D1 Mini (ESP8266)
- GY-521 (MPU-6050) gyroscope
- DS18B20 temperature sensor
- 18650 battery + charger
- Petling tube (or similar)
- 3D printed sled
```

**Build Guide**: See [iSpindel.de](https://www.ispindel.de)

**MQTT Configuration:**

iSpindel firmware supports MQTT directly. Configure via web interface:

```
Service Type: MQTT
Server: 192.168.1.100
Port: 1883
Username: tipsylab
Password: YourPassword
Topic: tipsylab/batch1/ispindel
```

**Message Format:**
```json
{
  "name": "iSpindel01",
  "ID": 123456,
  "angle": 45.3,
  "temperature": 20.5,
  "temp_units": "C",
  "battery": 3.95,
  "gravity": 1.042,
  "interval": 900,
  "RSSI": -65
}
```

**TipsyHomeLab Configuration:**
```yaml
tipsyhomelab:
  batches:
    - name: "Batch 1"
      sensors:
        ispindel:
          topic: "tipsylab/batch1/ispindel"
          calibration:  # Polynomial coefficients
            - 0.0001217
            - -0.0064
            - 0.9994
```

**Calibration:**

1. Create calibration solutions:
   - Water: 1.000 SG
   - Sugar water: 1.020, 1.040, 1.060, 1.080 SG
2. Float iSpindel in each solution
3. Record angle for each
4. Use calibration spreadsheet to calculate polynomial
5. Enter coefficients in config

### Tilt Hydrometer

**Description**: Commercial Bluetooth hydrometer.

**Features:**
- Specific gravity
- Temperature
- Bluetooth BLE
- No calibration needed
- 6-12 month battery life

**Integration:**

Requires Raspberry Pi or ESP32 as BLE bridge.

**Using Tilt Pi:**
```bash
# Install Tilt Pi
wget -O install.sh https://www.tilthydrometer.com/install.sh
sudo sh install.sh

# Configure MQTT output
sudo nano /home/pi/tilt_mqtt.conf
```

Config:
```ini
[mqtt]
broker = 192.168.1.100
port = 1883
username = tipsylab
password = YourPassword
topic_prefix = tipsylab/batch1/tilt
```

**Message Format:**
```json
{
  "color": "orange",
  "gravity": 1.042,
  "temperature": 68,
  "temp_units": "F",
  "rssi": -75,
  "battery": 90
}
```

**TipsyHomeLab Configuration:**
```yaml
sensors:
  tilt:
    topic: "tipsylab/batch1/tilt"
    color: "orange"
    temp_units: "F"
```

---

## Temperature Sensors

Critical for accurate gravity compensation and fermentation control.

### DS18B20 Digital Sensor

**Description**: 1-Wire digital temperature sensor.

**Specs:**
- Accuracy: ±0.5°C
- Range: -55°C to +125°C
- Resolution: 0.0625°C (12-bit)
- Waterproof versions available

**Wiring (Single Sensor):**
```
DS18B20          ESP8266
--------         -------
VDD (Red)   ───→  3.3V
GND (Black) ───→  GND
DATA (Yellow)───→ D4 (GPIO2)
                   │
                [4.7kΩ] ← Pull-up resistor to 3.3V
```

**Wiring (Multiple Sensors):**
```
     3.3V
       │
    [4.7kΩ]
       │
       ├────────┬────────┬────────  D4 (GPIO2)
       │        │        │
    [DS1]    [DS2]    [DS3]
       │        │        │
       └────────┴────────┴────────  GND
```

**Code:**
```cpp
#include <OneWire.h>
#include <DallasTemperature.h>

#define ONE_WIRE_BUS D4

OneWire oneWire(ONE_WIRE_BUS);
DallasTemperature sensors(&oneWire);

void setup() {
  Serial.begin(115200);
  sensors.begin();
}

void loop() {
  sensors.requestTemperatures();
  float tempC = sensors.getTempCByIndex(0);

  // Publish to MQTT
  StaticJsonDocument<100> doc;
  doc["temperature"] = tempC;
  doc["units"] = "C";
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  client.publish("tipsylab/batch1/temp", buffer);

  delay(60000);  // Read every minute
}
```

**Thermowell Installation:**

For accurate wort temperature:

```
Fermentation Vessel
┌──────────────────┐
│                  │
│   ╔════════╗     │  ← Wort level
│   ║        ║     │
│   ║  Must  ║     │
│   ║        ║     │
│   ║   ┌────║─────┼──── Thermowell (stainless steel tube)
│   ║   │ DS │     │
│   ║   │18B2│     │      Inside: DS18B20 sensor
│   ║   │ 0  │     │
│   ║   └────║─────┤
│   ╚════════╝     │
└──────────────────┘
```

Benefits:
- Accurate wort temperature
- No contamination risk
- Easy to remove for cleaning

---

## pH Sensors

For advanced monitoring and process control.

### Atlas Scientific pH Sensor

**Description**: Laboratory-grade pH measurement.

**Hardware:**
```
Required ($150-200):
- Atlas Scientific pH circuit (EZO)
- Atlas Scientific pH probe
- BNC connector
- Calibration solutions (pH 4, 7, 10)
```

**Wiring (I2C):**
```
Atlas pH         ESP8266
--------         -------
VCC       ───→   3.3V
GND       ───→   GND
SDA       ───→   D2 (GPIO4)
SCL       ───→   D1 (GPIO5)
```

**Code:**
```cpp
#include <Wire.h>

#define PH_ADDRESS 99  // Default I2C address

void setup() {
  Wire.begin();
  Serial.begin(115200);
}

float readpH() {
  Wire.beginTransmission(PH_ADDRESS);
  Wire.write('R');  // Request reading
  Wire.endTransmission();

  delay(1000);  // Wait for reading

  Wire.requestFrom(PH_ADDRESS, 20, 1);
  char response[20];
  byte i = 0;

  while (Wire.available()) {
    response[i] = Wire.read();
    i++;
  }

  return atof(response);
}

void loop() {
  float ph = readpH();

  // Publish to MQTT
  StaticJsonDocument<100> doc;
  doc["ph"] = ph;
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  client.publish("tipsylab/batch1/ph", buffer);

  delay(300000);  // Read every 5 minutes
}
```

**Calibration:**

```cpp
// Three-point calibration
Wire.write("Cal,mid,7.00");   // pH 7 solution
// ... wait and rinse ...
Wire.write("Cal,low,4.00");   // pH 4 solution
// ... wait and rinse ...
Wire.write("Cal,high,10.00"); // pH 10 solution
```

**Maintenance:**
- Store probe in storage solution (NOT distilled water)
- Calibrate monthly
- Clean with warm water after each use
- Replace probe every 12-18 months

---

## Pressure Sensors

Essential for Pet Nat safety monitoring.

### Pressure Transducer

**Description**: Measure CO2 pressure in sealed vessels.

**WARNING**: Only use with pressure-rated bottles. Always follow safety guidelines.

**Hardware:**
```
Recommended ($40-60):
- 0-10 bar pressure transducer (4-20mA or 0-5V output)
- Stainless steel for food safety
- 1/4" NPT thread
- Appropriate fittings for bottle cap
```

**Wiring (0-5V Transducer):**
```
Transducer       ESP32 (3.3V ADC)
----------       ----------------
V+ (12-24V) ─→   External power supply +
GND         ─→   Common ground
VOUT        ─→   Voltage divider ─→ GPIO34
                      │
                   [10kΩ]
                      │
                   [20kΩ]
                      │
                     GND
```

**Voltage Divider** (to protect 3.3V ADC):
```
5V signal ──[10kΩ]──┬──→ ESP32 ADC (max 3.3V)
                    │
                 [20kΩ]
                    │
                   GND

Output: 5V × (20kΩ / 30kΩ) = 3.33V (safe for ESP32)
```

**Code:**
```cpp
const int PRESSURE_PIN = 34;  // ADC pin
const float V_REF = 3.3;
const float ADC_MAX = 4095.0;  // 12-bit ADC
const float PRESSURE_MAX = 10.0;  // bar
const float VOLTAGE_DIVIDER = 0.667;  // 20kΩ / 30kΩ

float readPressure() {
  int rawValue = analogRead(PRESSURE_PIN);
  float voltage = (rawValue / ADC_MAX) * V_REF;
  float actualVoltage = voltage / VOLTAGE_DIVIDER;
  float pressure = (actualVoltage / 5.0) * PRESSURE_MAX;

  return pressure;
}

void loop() {
  float pressure = readPressure();

  // Safety check
  if (pressure > 6.0) {  // Maximum safe pressure for champagne bottles
    // ALERT! Dangerous pressure
    client.publish("tipsylab/batch1/alert", "DANGER: High pressure!");
  }

  // Publish reading
  StaticJsonDocument<100> doc;
  doc["pressure"] = pressure;
  doc["units"] = "bar";
  doc["timestamp"] = millis();

  char buffer[100];
  serializeJson(doc, buffer);
  client.publish("tipsylab/batch1/pressure", buffer);

  delay(60000);  // Read every minute
}
```

**Mounting:**

```
Bottle Cap Modification:
┌─────────────┐
│   Cap Top   │
│      ●      │  ← Drill hole for fitting
├─────────────┤
│   Gasket    │
├─────────────┤
│  [Fitting]  │  ← 1/4" NPT to barb
│      │      │
│   [Tube]    │  ← Pressure-rated tubing
│      │      │
│ [Transducer]│  ← Mount outside bottle
└─────────────┘
```

**Calibration:**
1. Zero pressure (atmospheric): Note reading
2. Apply known pressure with regulator
3. Calculate linear calibration factor
4. Test with accurate gauge

---

## MQTT Topics

### Topic Structure

TipsyHomeLab uses hierarchical MQTT topics:

```
tipsylab/
├── [batch_id]/
│   ├── bubbles          # Bubble counter data
│   ├── ispindel         # iSpindel full message
│   ├── tilt             # Tilt hydrometer
│   ├── temperature      # Temperature sensor
│   ├── gravity          # Specific gravity (standalone)
│   ├── ph               # pH sensor
│   ├── pressure         # Pressure sensor
│   ├── status           # Batch status updates
│   └── alerts           # Alert messages
└── system/
    ├── status           # System health
    └── config           # Configuration updates
```

### Message Formats

#### Bubble Counter
**Topic**: `tipsylab/[batch_id]/bubbles`

**Payload**:
```json
{
  "count": 1234,
  "timestamp": 1699999999000,
  "interval": 1250,
  "rate": 48.0
}
```

**Fields**:
- `count`: Total bubbles since start (integer)
- `timestamp`: Unix timestamp in milliseconds
- `interval`: Time since last bubble in milliseconds (optional)
- `rate`: Current rate in bubbles/minute (optional)

#### iSpindel
**Topic**: `tipsylab/[batch_id]/ispindel`

**Payload**:
```json
{
  "name": "iSpindel01",
  "ID": 123456,
  "angle": 45.3,
  "temperature": 20.5,
  "temp_units": "C",
  "battery": 3.95,
  "gravity": 1.042,
  "interval": 900,
  "RSSI": -65
}
```

#### Temperature
**Topic**: `tipsylab/[batch_id]/temperature`

**Payload**:
```json
{
  "temperature": 20.5,
  "units": "C",
  "sensor_id": "ds18b20_1",
  "timestamp": 1699999999000
}
```

#### Pressure
**Topic**: `tipsylab/[batch_id]/pressure`

**Payload**:
```json
{
  "pressure": 3.2,
  "units": "bar",
  "temperature": 20.5,
  "timestamp": 1699999999000
}
```

#### pH
**Topic**: `tipsylab/[batch_id]/ph`

**Payload**:
```json
{
  "ph": 3.45,
  "temperature": 20.5,
  "timestamp": 1699999999000
}
```

### QoS and Retention

**Recommended Settings**:
- **QoS 1**: At least once delivery (reliable)
- **Retained**: Yes for latest state
- **Keep-alive**: 60 seconds

**Publishing**:
```cpp
client.publish(topic, payload, true);  // Retained = true
```

**Subscribing**:
```cpp
client.subscribe("tipsylab/batch1/#", 1);  // QoS 1
```

---

## Calibration

### Bubble Counter Calibration

1. **Baseline Test**:
   - Use CO2 injection or manual puffing
   - Count visual bubbles vs. sensor counts
   - Adjust sensitivity threshold

2. **False Positive Test**:
   - Leave sensor on still airlock
   - Should register 0 bubbles
   - Adjust debounce timing

3. **Fast Fermentation Test**:
   - Test with active fermentation (>60 bubbles/min)
   - Verify no missed bubbles
   - May need faster sampling rate

### iSpindel Calibration

See [Calibration Spreadsheet](https://docs.google.com/spreadsheets/d/1kGY0WaFbNLkVoS88VVLdAVhQO5Cxp6FvVKP1kAFPRhc/)

**Process**:
1. Prepare calibration solutions
2. Float iSpindel, record angle
3. Create polynomial equation
4. Validate with refractometer

**Typical Coefficients**:
```yaml
calibration:  # Gravity = c[0]*angle³ + c[1]*angle² + c[2]*angle + c[3]
  - 0.00001217   # angle³ coefficient
  - -0.0064      # angle² coefficient
  - 0.0912       # angle coefficient
  - 0.9994       # constant
```

### Temperature Calibration

DS18B20 sensors are pre-calibrated, but verify:

```cpp
// Ice water test (should read 0°C)
sensors.requestTemperatures();
float iceTemp = sensors.getTempCByIndex(0);
Serial.println(iceTemp);  // Should be ~0.0°C

// Boiling water test (should read 100°C at sea level)
float boilTemp = sensors.getTempCByIndex(0);
Serial.println(boilTemp);  // Should be ~100.0°C

// Apply offset if needed
float correctedTemp = readTemp - 0.5;  // If sensor reads 0.5°C high
```

---

## Troubleshooting

### Bubble Counter Issues

**Problem**: No bubbles detected

**Solutions**:
1. Check LED is working (use phone camera to see IR)
2. Verify photodiode wiring
3. Adjust threshold value
4. Ensure bubble passes through beam
5. Check power supply

**Problem**: False bubbles

**Solutions**:
1. Increase debounce time
2. Adjust threshold
3. Shield from ambient light
4. Check for loose connections
5. Verify airlock is sealed

### iSpindel Issues

**Problem**: Wrong gravity readings

**Solutions**:
1. Recalibrate with sugar solutions
2. Check polynomial coefficients
3. Verify not stuck to vessel wall
4. Ensure properly floating
5. Check temperature compensation

**Problem**: Battery draining fast

**Solutions**:
1. Increase sleep interval (900s recommended)
2. Reduce WiFi transmission power
3. Check for failed connection attempts
4. Replace battery if old
5. Verify deep sleep is working

### Temperature Sensor Issues

**Problem**: Reading -127°C or 85°C

**Solutions**:
- Check connections (loose wire)
- Verify pull-up resistor
- Test with different GPIO pin
- Replace sensor if damaged

**Problem**: Fluctuating readings

**Solutions**:
- Add delay between readings
- Use averaging: `(t1 + t2 + t3) / 3`
- Check power supply stability
- Shield cable from interference

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more issues and solutions.

---

## Additional Resources

- [iSpindel Official Documentation](https://www.ispindel.de)
- [Tilt Hydrometer Guide](https://tilthydrometer.com)
- [Atlas Scientific pH Guide](https://atlas-scientific.com)
- [ESP8266 Arduino Core](https://github.com/esp8266/Arduino)
- [Home Assistant MQTT](https://www.home-assistant.io/integrations/mqtt/)

---

## Safety Considerations

1. **Electrical Safety**:
   - Use proper wire gauges
   - Insulate all connections
   - Keep electronics away from liquids
   - Use GFCI-protected outlets

2. **Food Safety**:
   - Use food-grade materials only
   - Stainless steel for liquid contact
   - Sanitize all equipment
   - Avoid lead-containing solder

3. **Pressure Safety**:
   - Never exceed bottle pressure ratings
   - Use champagne bottles for Pet Nat (rated to 6+ bar)
   - Install pressure relief valves
   - Monitor pressure frequently
   - Wear safety glasses when handling pressurized vessels

4. **Chemical Safety**:
   - Handle pH probe storage solution carefully
   - Dispose of calibration solutions properly
   - Keep sensors away from children/pets
