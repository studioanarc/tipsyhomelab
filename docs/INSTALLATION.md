# Installation Guide

This guide covers everything you need to get TipsyHomeLab up and running, from prerequisites to advanced configurations.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [MQTT Broker Setup](#mqtt-broker-setup)
3. [Installation Methods](#installation-methods)
4. [Initial Configuration](#initial-configuration)
5. [Sensor Setup](#sensor-setup)
6. [Dashboard Configuration](#dashboard-configuration)
7. [Testing & Verification](#testing--verification)
8. [Next Steps](#next-steps)

---

## Prerequisites

### Required

- **Home Assistant**: Version 2023.1 or newer
  - Core, Supervised, or OS installation
  - Adequate storage for historical data (minimum 1GB recommended)
- **MQTT Broker**: Mosquitto or compatible MQTT server
  - Can be local or remote
  - Port 1883 (standard) or 8883 (TLS)
- **Network Connectivity**: Sensors must reach MQTT broker
- **Python**: 3.9 or newer (included with Home Assistant)

### Recommended

- **Backup System**: Automated backups of Home Assistant
- **UPS**: Uninterruptible power supply for continuous monitoring
- **Static IP**: For Home Assistant and MQTT broker
- **Dedicated Hardware**: Raspberry Pi 4 or better for optimal performance

### Optional

- **InfluxDB**: For long-term data storage and analysis
- **Grafana**: Advanced visualization and analytics
- **Node-RED**: Complex automation workflows

---

## MQTT Broker Setup

TipsyHomeLab requires an MQTT broker. If you don't have one set up, follow these steps.

### Option 1: Mosquitto Add-on (Easiest)

1. Navigate to **Supervisor → Add-on Store**
2. Search for "Mosquitto broker"
3. Click **Install**
4. Go to **Configuration** tab:

```yaml
logins:
  - username: tipsylab
    password: YourSecurePassword123

customize:
  active: false
  folder: mosquitto

certfile: fullchain.pem
keyfile: privkey.pem
require_certificate: false
```

5. Click **Save**
6. Go to **Info** tab and click **Start**
7. Enable **Start on boot**

### Option 2: External Mosquitto Broker

If running Mosquitto on a separate machine:

```bash
# Install Mosquitto
sudo apt-get update
sudo apt-get install mosquitto mosquitto-clients

# Create password file
sudo mosquitto_passwd -c /etc/mosquitto/passwd tipsylab

# Configure Mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
```

Add to config:
```
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Restart Mosquitto:
```bash
sudo systemctl restart mosquitto
sudo systemctl enable mosquitto
```

### Configure Home Assistant MQTT Integration

1. Go to **Configuration → Integrations**
2. Click **Add Integration**
3. Search for "MQTT"
4. Enter broker details:
   - **Broker**: localhost (or IP address)
   - **Port**: 1883
   - **Username**: tipsylab
   - **Password**: YourSecurePassword123
5. Click **Submit**

### Test MQTT Connection

```bash
# Subscribe to test topic
mosquitto_sub -h localhost -u tipsylab -P YourSecurePassword123 -t test/topic

# In another terminal, publish test message
mosquitto_pub -h localhost -u tipsylab -P YourSecurePassword123 -t test/topic -m "Hello TipsyLab!"
```

---

## Installation Methods

### Method 1: HACS Installation (Recommended)

HACS (Home Assistant Community Store) makes installation and updates easy.

#### Install HACS (if not already installed)

1. Download HACS:
```bash
wget -O - https://get.hacs.xyz | bash -
```

2. Restart Home Assistant
3. Add HACS integration via UI
4. Authenticate with GitHub

#### Install TipsyHomeLab via HACS

1. Open **HACS** in Home Assistant sidebar
2. Click **Integrations**
3. Click the **⋮** menu (top right)
4. Select **Custom repositories**
5. Add repository:
   - **URL**: `https://github.com/yourusername/tipsyhomelab`
   - **Category**: Integration
6. Click **Add**
7. Click **Explore & Download Repositories**
8. Search for "TipsyHomeLab"
9. Click **Download**
10. Select latest version
11. Restart Home Assistant

### Method 2: Manual Installation

For advanced users or when HACS is not available.

#### Download Release

```bash
# Navigate to custom_components directory
cd /config/custom_components

# Download latest release
wget https://github.com/yourusername/tipsyhomelab/releases/latest/download/tipsyhomelab.zip

# Extract
unzip tipsyhomelab.zip

# Verify installation
ls -la tipsyhomelab/
```

Expected directory structure:
```
custom_components/
└── tipsyhomelab/
    ├── __init__.py
    ├── manifest.json
    ├── sensor.py
    ├── config_flow.py
    ├── const.py
    ├── ml/
    │   ├── predictor.py
    │   └── models/
    └── translations/
        └── en.json
```

#### Set Permissions

```bash
# Ensure correct ownership
chown -R homeassistant:homeassistant /config/custom_components/tipsyhomelab

# Set correct permissions
chmod -R 755 /config/custom_components/tipsyhomelab
```

#### Restart Home Assistant

```bash
# From terminal
ha core restart

# Or use UI: Configuration → Server Controls → Restart
```

### Method 3: Git Clone (Development)

For developers or testing latest features.

```bash
cd /config/custom_components
git clone https://github.com/yourusername/tipsyhomelab.git
cd tipsyhomelab
git checkout main  # or development branch
```

---

## Initial Configuration

### Step 1: Add Integration via UI

1. Go to **Configuration → Integrations**
2. Click **Add Integration**
3. Search for "TipsyHomeLab"
4. Click to add

### Step 2: Configuration Wizard

The setup wizard will guide you through initial configuration.

**Basic Information:**
- **Batch Name**: Name for your fermentation batch
- **Batch Type**: Select from:
  - Pet Nat (Pétillant Naturel)
  - Beer
  - Wine (still)
  - Cider
  - Kombucha
  - Custom

**MQTT Settings:**
- **Broker**: Usually `localhost`
- **Port**: Usually `1883`
- **Username**: Your MQTT username
- **Password**: Your MQTT password
- **Topic Prefix**: e.g., `tipsylab/batch1`

**Sensor Configuration:**
- Select which sensors you have available
- Configure MQTT topics for each sensor

**Advanced Options:**
- Enable predictions
- Set target values (gravity, pressure, etc.)
- Configure alert thresholds

### Step 3: Configuration YAML (Alternative)

Or configure via `configuration.yaml`:

```yaml
# Minimal configuration
tipsyhomelab:
  mqtt:
    broker: localhost
    port: 1883
    username: !secret mqtt_username
    password: !secret mqtt_password

  batches:
    - name: "My First Batch"
      type: petnat
      sensors:
        bubble_counter: "tipsylab/batch1/bubbles"
        temperature: "tipsylab/batch1/temp"
```

Add credentials to `secrets.yaml`:
```yaml
mqtt_username: tipsylab
mqtt_password: YourSecurePassword123
```

### Step 4: Restart and Verify

1. Restart Home Assistant
2. Check logs for errors:
   ```
   Configuration → Logs
   ```
3. Look for TipsyHomeLab entries

---

## Sensor Setup

See [SENSORS.md](SENSORS.md) for detailed sensor setup guides.

### Quick Setup: Bubble Counter

Most basic setup using ESP8266/ESP32 with optical sensor.

**Hardware:**
- ESP8266 or ESP32
- IR LED and photodiode
- Resistors (220Ω for LED, 10kΩ for photodiode)
- Airlock for fermentation vessel

**Wiring:**
```
ESP8266          Component
--------         ---------
3.3V      ───┬──→ IR LED anode
            │
D1        ──┴──→ 220Ω resistor → IR LED cathode
D2        ───────→ Photodiode anode
GND       ───┬──→ Photodiode cathode
            │
            └──→ 10kΩ pull-down resistor
```

**Arduino Code:**
```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>

const char* ssid = "YourWiFi";
const char* password = "YourPassword";
const char* mqtt_server = "192.168.1.100";
const char* mqtt_topic = "tipsylab/batch1/bubbles";

WiFiClient espClient;
PubSubClient client(espClient);

const int sensorPin = D2;
int bubbleCount = 0;
unsigned long lastBubble = 0;
int lastState = LOW;

void setup() {
  Serial.begin(115200);
  pinMode(sensorPin, INPUT);

  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  client.setServer(mqtt_server, 1883);
}

void loop() {
  if (!client.connected()) {
    reconnect();
  }
  client.loop();

  int currentState = digitalRead(sensorPin);

  // Detect bubble (rising edge)
  if (currentState == HIGH && lastState == LOW) {
    unsigned long now = millis();
    if (now - lastBubble > 100) {  // Debounce
      bubbleCount++;

      // Publish bubble event
      String payload = "{\"count\":" + String(bubbleCount) +
                      ",\"timestamp\":" + String(now) + "}";
      client.publish(mqtt_topic, payload.c_str());

      lastBubble = now;
    }
  }

  lastState = currentState;
  delay(10);
}

void reconnect() {
  while (!client.connected()) {
    if (client.connect("TipsyLabSensor")) {
      Serial.println("MQTT Connected");
    } else {
      delay(5000);
    }
  }
}
```

Flash to ESP8266 and place sensor on airlock.

---

## Dashboard Configuration

### Add Lovelace Cards

1. Edit your dashboard (click **⋮** → **Edit Dashboard**)
2. Click **Add Card**
3. Search for "TipsyHomeLab" cards or use manual YAML

### Example Dashboard Card

```yaml
type: entities
title: Fermentation Monitor
entities:
  - entity: sensor.tipsylab_batch1_bubble_rate
    name: Bubble Rate
    icon: mdi:water
  - entity: sensor.tipsylab_batch1_gravity
    name: Specific Gravity
  - entity: sensor.tipsylab_batch1_temperature
    name: Temperature
  - entity: sensor.tipsylab_batch1_abv
    name: ABV
  - entity: sensor.tipsylab_batch1_days_remaining
    name: Est. Days to Completion
```

### History Graph

```yaml
type: history-graph
title: Fermentation Activity (48h)
entities:
  - entity: sensor.tipsylab_batch1_bubble_rate
    name: Bubbles/min
hours_to_show: 48
refresh_interval: 60
```

See [examples/dashboard_examples/](../examples/dashboard_examples/) for complete dashboard configurations.

---

## Testing & Verification

### Verify Integration Loaded

1. Check integration status:
   - **Configuration → Integrations**
   - Look for "TipsyHomeLab" with green status

2. Check entities:
   - **Configuration → Entities**
   - Filter by "tipsylab"
   - Should see all configured sensors

### Test MQTT Communication

```bash
# Monitor MQTT topics
mosquitto_sub -h localhost -u tipsylab -P YourPassword -t tipsylab/# -v

# Simulate sensor data
mosquitto_pub -h localhost -u tipsylab -P YourPassword \
  -t tipsylab/batch1/bubbles \
  -m '{"count":1,"timestamp":1234567890}'
```

### Check Logs

Look for successful initialization:

```
Configuration → Logs

Expected entries:
[custom_components.tipsyhomelab] Successfully initialized
[custom_components.tipsyhomelab] Connected to MQTT broker
[custom_components.tipsyhomelab] Loaded batch: My First Batch
[custom_components.tipsyhomelab] Sensors configured: bubble_counter, temperature
```

### Verify Data Flow

1. Generate test bubble (or simulate via MQTT)
2. Check sensor updates in UI
3. View history graph
4. Confirm data is being stored

---

## Next Steps

After successful installation:

1. **Calibrate Sensors**: See [SENSORS.md](SENSORS.md#calibration)
2. **Configure Predictions**: See [ML_MODELS.md](ML_MODELS.md)
3. **Set Up Alerts**: Create automations for notifications
4. **Create Dashboards**: Design your perfect monitoring interface
5. **Start Fermentation**: Begin your first monitored batch!

---

## Common Installation Issues

### Integration Not Appearing

**Symptom**: TipsyHomeLab doesn't show in integrations list

**Solutions**:
1. Clear browser cache (Ctrl+Shift+R)
2. Check file permissions
3. Verify all files copied correctly
4. Check Home Assistant logs for errors
5. Restart Home Assistant fully (not just reload)

### MQTT Connection Failed

**Symptom**: "Failed to connect to MQTT broker"

**Solutions**:
1. Verify broker is running: `sudo systemctl status mosquitto`
2. Check firewall rules
3. Test with mosquitto_sub/pub
4. Verify credentials in secrets.yaml
5. Check broker logs: `sudo journalctl -u mosquitto -f`

### Sensors Not Updating

**Symptom**: Sensor entities show "unavailable"

**Solutions**:
1. Verify MQTT topics match configuration
2. Check sensor is publishing data
3. Monitor MQTT with `mosquitto_sub`
4. Verify retained messages: `-t topic -v -d`
5. Check sensor battery/power

### Python Dependencies Missing

**Symptom**: Import errors in logs

**Solutions**:
```bash
# Enter Home Assistant container
docker exec -it homeassistant /bin/bash

# Install dependencies
pip install -r /config/custom_components/tipsyhomelab/requirements.txt
```

---

## Upgrade Instructions

### Via HACS

1. Open HACS → Integrations
2. Find TipsyHomeLab
3. Click **Update** if available
4. Restart Home Assistant

### Manual Upgrade

1. Backup current configuration
2. Download new release
3. Stop Home Assistant
4. Replace files in `custom_components/tipsyhomelab/`
5. Start Home Assistant
6. Check logs for migration messages

### Breaking Changes

Always check [CHANGELOG.md](../CHANGELOG.md) before upgrading for breaking changes and migration guides.

---

## Uninstallation

### Remove Integration

1. **Configuration → Integrations**
2. Find TipsyHomeLab
3. Click **⋮** → **Delete**
4. Confirm deletion

### Remove Files

```bash
rm -rf /config/custom_components/tipsyhomelab
```

### Clean Up

1. Remove configuration from `configuration.yaml`
2. Remove dashboard cards
3. Remove automations
4. Optionally remove MQTT topics:
   ```bash
   mosquitto_pub -h localhost -u user -P pass -t tipsylab/batch1 -n -r
   ```

---

## Getting Help

If you encounter issues not covered here:

1. Check [Troubleshooting Guide](TROUBLESHOOTING.md)
2. Search [GitHub Issues](https://github.com/yourusername/tipsyhomelab/issues)
3. Ask in [Discussions](https://github.com/yourusername/tipsyhomelab/discussions)
4. Join our [Discord Community](https://discord.gg/tipsyhomelab)

When reporting issues, include:
- Home Assistant version
- Installation method
- Relevant logs
- Configuration (sanitized)
- Steps to reproduce
