# MQTT API Documentation

Complete reference for the TipsyHomeLab MQTT API, including all message formats, topics, and integration examples.

---

## Table of Contents

1. [Overview](#overview)
2. [Topic Structure](#topic-structure)
3. [Message Formats](#message-formats)
4. [Publishing Data](#publishing-data)
5. [Subscribing to Data](#subscribing-to-data)
6. [Home Assistant Integration](#home-assistant-integration)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## Overview

TipsyHomeLab uses MQTT (Message Queuing Telemetry Transport) as its primary communication protocol. This allows:

- **Universal Sensor Support**: Any sensor that can publish MQTT
- **Decoupled Architecture**: Sensors don't need to know about Home Assistant
- **Scalability**: Add sensors without modifying core system
- **Flexibility**: Use any MQTT client or library
- **Reliability**: Built-in QoS and message retention

### MQTT Basics

**Key Concepts:**
- **Broker**: Central MQTT server (e.g., Mosquitto)
- **Topic**: Hierarchical message channel (e.g., `tipsylab/batch1/bubbles`)
- **Publish**: Send a message to a topic
- **Subscribe**: Receive messages from a topic
- **QoS**: Quality of Service (0=fire and forget, 1=at least once, 2=exactly once)
- **Retained**: Last message saved for new subscribers

---

## Topic Structure

### Hierarchy

```
tipsylab/
├── {batch_id}/
│   ├── bubbles              # Bubble counter data
│   ├── gravity              # Specific gravity readings
│   ├── temperature          # Temperature sensor(s)
│   ├── ph                   # pH sensor
│   ├── pressure             # Pressure sensor
│   ├── ispindel             # iSpindel complete message
│   ├── tilt/{color}         # Tilt hydrometer by color
│   ├── predictions/         # ML predictions
│   │   ├── completion       # Completion date prediction
│   │   ├── final_gravity    # Final gravity prediction
│   │   ├── bottle_pressure  # Bottle pressure prediction
│   │   └── confidence       # Prediction confidence metrics
│   ├── status               # Batch status
│   └── alerts               # Alert messages
├── system/
│   ├── status               # System health
│   ├── config               # Configuration updates
│   └── version              # Software version
└── discovery/
    └── {sensor_id}/config   # Home Assistant MQTT discovery
```

### Naming Conventions

**Batch IDs:**
- Use lowercase alphanumeric
- Separate words with underscores
- Examples: `batch1`, `pet_nat_spring_2024`, `fermenter_alpha`

**Topic Rules:**
- No spaces (use underscores)
- Avoid special characters except `-` and `_`
- Keep hierarchical (general → specific)
- Use plural for collections: `batches`, `sensors`

---

## Message Formats

All messages use JSON format unless otherwise specified.

### Bubble Counter

**Topic:** `tipsylab/{batch_id}/bubbles`

**Payload:**
```json
{
  "count": 1234,
  "timestamp": 1699999999000,
  "interval": 1250,
  "rate": 48.0,
  "sensor_id": "bubble_counter_1"
}
```

**Fields:**
| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `count` | integer | Yes | - | Total bubbles since start |
| `timestamp` | integer | Yes | ms | Unix timestamp in milliseconds |
| `interval` | integer | No | ms | Time since last bubble |
| `rate` | float | No | bubbles/min | Current bubble rate |
| `sensor_id` | string | No | - | Unique sensor identifier |

**Minimal Valid Message:**
```json
{"count": 1, "timestamp": 1699999999000}
```

### Gravity (Specific Gravity)

**Topic:** `tipsylab/{batch_id}/gravity`

**Payload:**
```json
{
  "gravity": 1.042,
  "temperature": 20.5,
  "temp_units": "C",
  "timestamp": 1699999999000,
  "sensor_id": "ispindel_1",
  "battery": 3.95
}
```

**Fields:**
| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `gravity` | float | Yes | SG | Specific gravity (1.000-1.200) |
| `temperature` | float | Recommended | C or F | Temperature at measurement |
| `temp_units` | string | If temp | C/F | Temperature unit |
| `timestamp` | integer | Yes | ms | Unix timestamp |
| `sensor_id` | string | No | - | Sensor identifier |
| `battery` | float | No | V | Battery voltage (for wireless sensors) |
| `angle` | float | No | degrees | Tilt angle (for iSpindel) |
| `rssi` | integer | No | dBm | WiFi signal strength |

**Example (iSpindel Full Message):**
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
  "RSSI": -65,
  "timestamp": 1699999999000
}
```

### Temperature

**Topic:** `tipsylab/{batch_id}/temperature`

**Payload:**
```json
{
  "temperature": 20.5,
  "units": "C",
  "timestamp": 1699999999000,
  "sensor_id": "ds18b20_wort",
  "placement": "wort"
}
```

**Fields:**
| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `temperature` | float | Yes | C or F | Temperature reading |
| `units` | string | Yes | C/F | Temperature unit |
| `timestamp` | integer | Yes | ms | Unix timestamp |
| `sensor_id` | string | No | - | Sensor identifier |
| `placement` | string | No | - | Sensor location (wort/ambient/chamber) |
| `humidity` | float | No | % | Relative humidity (if applicable) |

**Multiple Temperature Sensors:**
Use different topics:
```
tipsylab/batch1/temperature/wort
tipsylab/batch1/temperature/ambient
tipsylab/batch1/temperature/chamber
```

### pH

**Topic:** `tipsylab/{batch_id}/ph`

**Payload:**
```json
{
  "ph": 3.45,
  "temperature": 20.5,
  "timestamp": 1699999999000,
  "sensor_id": "atlas_ph_1",
  "calibrated": true,
  "last_calibration": "2024-11-01"
}
```

**Fields:**
| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `ph` | float | Yes | - | pH value (0-14) |
| `temperature` | float | Recommended | C | Temperature for compensation |
| `timestamp` | integer | Yes | ms | Unix timestamp |
| `sensor_id` | string | No | - | Sensor identifier |
| `calibrated` | boolean | No | - | Calibration status |
| `last_calibration` | string | No | ISO date | Last calibration date |

### Pressure

**Topic:** `tipsylab/{batch_id}/pressure`

**Payload:**
```json
{
  "pressure": 3.2,
  "units": "bar",
  "temperature": 20.5,
  "timestamp": 1699999999000,
  "sensor_id": "pressure_transducer_1"
}
```

**Fields:**
| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `pressure` | float | Yes | bar/psi | Pressure reading |
| `units` | string | Yes | bar/psi/kpa | Pressure unit |
| `temperature` | float | Recommended | C | Temperature at measurement |
| `timestamp` | integer | Yes | ms | Unix timestamp |
| `sensor_id` | string | No | - | Sensor identifier |

**Unit Conversions:**
- 1 bar = 14.5038 PSI
- 1 bar = 100 kPa
- 1 atmosphere = 1.01325 bar

### Predictions

**Topic:** `tipsylab/{batch_id}/predictions/completion`

**Payload:**
```json
{
  "predicted_date": "2024-11-20T14:30:00Z",
  "days_remaining": 8.5,
  "confidence": 0.85,
  "confidence_interval": {
    "lower": "2024-11-19T14:30:00Z",
    "upper": "2024-11-21T14:30:00Z"
  },
  "model_used": "gradient_boosting",
  "last_updated": 1699999999000
}
```

**Topic:** `tipsylab/{batch_id}/predictions/final_gravity`

**Payload:**
```json
{
  "predicted_gravity": 1.002,
  "confidence": 0.92,
  "confidence_interval": {
    "lower": 1.001,
    "upper": 1.003
  },
  "current_gravity": 1.018,
  "attenuation": 85.5,
  "last_updated": 1699999999000
}
```

**Topic:** `tipsylab/{batch_id}/predictions/bottle_pressure`

**Payload:**
```json
{
  "predicted_pressure": 3.2,
  "units": "bar",
  "temperature": 20.0,
  "confidence": 0.88,
  "confidence_interval": {
    "lower": 2.9,
    "upper": 3.5
  },
  "safe_for_bottling": true,
  "bottle_type": "champagne",
  "max_safe_pressure": 6.0,
  "last_updated": 1699999999000
}
```

### Status

**Topic:** `tipsylab/{batch_id}/status`

**Payload:**
```json
{
  "state": "active_fermentation",
  "phase": "peak",
  "days_elapsed": 4.5,
  "health": "healthy",
  "last_activity": 1699999999000,
  "sensors_online": ["bubble_counter", "temperature", "ispindel"],
  "sensors_offline": []
}
```

**Valid States:**
- `lag_phase` - Yeast acclimating, minimal activity
- `active_fermentation` - Primary fermentation underway
- `peak_fermentation` - Maximum fermentation activity
- `slowing_fermentation` - Activity decreasing
- `finishing` - Near completion
- `complete` - Fermentation finished
- `stuck` - Fermentation stopped prematurely
- `bottling_window` - Ready to bottle (Pet Nat)
- `bottled` - Batch bottled
- `unknown` - Unable to determine state

### Alerts

**Topic:** `tipsylab/{batch_id}/alerts`

**Payload:**
```json
{
  "alert_type": "high_pressure",
  "severity": "warning",
  "message": "Pressure reached 5.5 bar - approaching maximum safe pressure",
  "value": 5.5,
  "threshold": 5.5,
  "timestamp": 1699999999000,
  "acknowledged": false
}
```

**Severity Levels:**
- `info` - Informational only
- `warning` - Attention needed
- `error` - Problem detected
- `critical` - Immediate action required

---

## Publishing Data

### Python Example

```python
import paho.mqtt.client as mqtt
import json
import time

# Connect to MQTT broker
client = mqtt.Client("bubble_counter_1")
client.username_pw_set("tipsylab", "password")
client.connect("localhost", 1883, 60)

# Publish bubble count
def publish_bubble(count):
    topic = "tipsylab/batch1/bubbles"

    payload = {
        "count": count,
        "timestamp": int(time.time() * 1000),
        "sensor_id": "bubble_counter_1"
    }

    # Publish with QoS 1 and retained flag
    result = client.publish(
        topic,
        json.dumps(payload),
        qos=1,
        retain=True
    )

    if result.rc == 0:
        print(f"Published bubble #{count}")
    else:
        print(f"Failed to publish: {result.rc}")

# Publish bubbles
for i in range(1, 101):
    publish_bubble(i)
    time.sleep(1)  # 1 bubble per second

client.disconnect()
```

### Arduino/ESP8266 Example

```cpp
#include <ESP8266WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

const char* ssid = "YourWiFi";
const char* password = "YourPassword";
const char* mqtt_server = "192.168.1.100";
const char* mqtt_user = "tipsylab";
const char* mqtt_pass = "password";

WiFiClient espClient;
PubSubClient client(espClient);

void publishTemperature(float temp) {
  const char* topic = "tipsylab/batch1/temperature";

  // Create JSON payload
  StaticJsonDocument<200> doc;
  doc["temperature"] = temp;
  doc["units"] = "C";
  doc["timestamp"] = millis();
  doc["sensor_id"] = "ds18b20_1";
  doc["placement"] = "wort";

  char buffer[200];
  serializeJson(doc, buffer);

  // Publish with retain flag
  client.publish(topic, buffer, true);

  Serial.print("Published temperature: ");
  Serial.println(temp);
}

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  client.setServer(mqtt_server, 1883);

  // Connect to MQTT
  while (!client.connected()) {
    if (client.connect("temp_sensor_1", mqtt_user, mqtt_pass)) {
      Serial.println("MQTT Connected");
    } else {
      delay(5000);
    }
  }
}

void loop() {
  if (!client.connected()) {
    // Reconnect logic here
  }
  client.loop();

  float temperature = readTemperatureSensor();
  publishTemperature(temperature);

  delay(60000);  // Publish every minute
}
```

### Node-RED Example

```json
[
    {
        "id": "mqtt_publish",
        "type": "mqtt out",
        "topic": "tipsylab/batch1/bubbles",
        "qos": "1",
        "retain": "true",
        "broker": "mqtt_broker",
        "name": "Publish Bubbles"
    },
    {
        "id": "format_message",
        "type": "function",
        "func": "msg.payload = {\n    count: flow.get('bubbleCount') || 0,\n    timestamp: Date.now(),\n    sensor_id: 'bubble_counter_1'\n};\nreturn msg;",
        "outputs": 1,
        "wires": [["mqtt_publish"]]
    }
]
```

---

## Subscribing to Data

### Python Example

```python
import paho.mqtt.client as mqtt
import json

def on_connect(client, userdata, flags, rc):
    print(f"Connected with result code {rc}")

    # Subscribe to all topics for batch1
    client.subscribe("tipsylab/batch1/#")

def on_message(client, userdata, msg):
    print(f"Topic: {msg.topic}")
    print(f"Payload: {msg.payload.decode()}")

    try:
        data = json.loads(msg.payload.decode())

        if "bubbles" in msg.topic:
            handle_bubble_data(data)
        elif "gravity" in msg.topic:
            handle_gravity_data(data)
        elif "temperature" in msg.topic:
            handle_temperature_data(data)

    except json.JSONDecodeError:
        print("Invalid JSON")

def handle_bubble_data(data):
    count = data['count']
    rate = data.get('rate', 0)
    print(f"Bubble count: {count}, Rate: {rate}/min")

def handle_gravity_data(data):
    gravity = data['gravity']
    temp = data.get('temperature', 'N/A')
    print(f"Gravity: {gravity}, Temp: {temp}")

def handle_temperature_data(data):
    temp = data['temperature']
    units = data['units']
    print(f"Temperature: {temp}{units}")

# Setup client
client = mqtt.Client()
client.username_pw_set("tipsylab", "password")
client.on_connect = on_connect
client.on_message = on_message

# Connect and subscribe
client.connect("localhost", 1883, 60)
client.loop_forever()
```

### JavaScript Example

```javascript
const mqtt = require('mqtt');

// Connect to broker
const client = mqtt.connect('mqtt://localhost:1883', {
    username: 'tipsylab',
    password: 'password'
});

client.on('connect', () => {
    console.log('Connected to MQTT broker');

    // Subscribe to all batch1 topics
    client.subscribe('tipsylab/batch1/#', (err) => {
        if (!err) {
            console.log('Subscribed to batch1 topics');
        }
    });
});

client.on('message', (topic, message) => {
    console.log(`Received message on ${topic}`);

    try {
        const data = JSON.parse(message.toString());

        if (topic.includes('bubbles')) {
            console.log(`Bubble count: ${data.count}`);
        } else if (topic.includes('gravity')) {
            console.log(`Gravity: ${data.gravity}`);
        } else if (topic.includes('temperature')) {
            console.log(`Temperature: ${data.temperature}${data.units}`);
        }

    } catch (e) {
        console.error('Invalid JSON:', e);
    }
});
```

---

## Home Assistant Integration

### MQTT Discovery

TipsyHomeLab automatically configures Home Assistant entities via MQTT discovery.

**Discovery Topic Format:**
```
homeassistant/{component}/{node_id}/{object_id}/config
```

**Example Discovery Message:**

**Topic:** `homeassistant/sensor/tipsylab_batch1/bubble_rate/config`

**Payload:**
```json
{
  "name": "Batch 1 Bubble Rate",
  "unique_id": "tipsylab_batch1_bubble_rate",
  "state_topic": "tipsylab/batch1/bubbles",
  "value_template": "{{ value_json.rate }}",
  "unit_of_measurement": "bubbles/min",
  "icon": "mdi:water",
  "device_class": "frequency",
  "device": {
    "identifiers": ["tipsylab_batch1"],
    "name": "Batch 1 Fermentation",
    "model": "TipsyHomeLab",
    "manufacturer": "TipsyHomeLab"
  }
}
```

### Manual Sensor Configuration

Add to `configuration.yaml`:

```yaml
mqtt:
  sensor:
    # Bubble Rate
    - name: "Batch 1 Bubble Rate"
      state_topic: "tipsylab/batch1/bubbles"
      value_template: "{{ value_json.rate }}"
      unit_of_measurement: "bubbles/min"
      icon: "mdi:water"

    # Gravity
    - name: "Batch 1 Gravity"
      state_topic: "tipsylab/batch1/gravity"
      value_template: "{{ value_json.gravity }}"
      unit_of_measurement: "SG"
      icon: "mdi:gauge"

    # Temperature
    - name: "Batch 1 Temperature"
      state_topic: "tipsylab/batch1/temperature"
      value_template: "{{ value_json.temperature }}"
      unit_of_measurement: "°C"
      device_class: "temperature"

    # Predicted Completion
    - name: "Batch 1 Completion Date"
      state_topic: "tipsylab/batch1/predictions/completion"
      value_template: "{{ value_json.predicted_date }}"
      icon: "mdi:calendar-clock"

  binary_sensor:
    # Fermentation Active
    - name: "Batch 1 Active"
      state_topic: "tipsylab/batch1/status"
      value_template: >
        {% if value_json.state in ['active_fermentation', 'peak_fermentation'] %}
          ON
        {% else %}
          OFF
        {% endif %}
      device_class: "running"
```

---

## Examples

### Complete ESP32 Bubble Counter

See [examples/mqtt_examples/esp32_bubble_counter.ino](../examples/mqtt_examples/esp32_bubble_counter.ino)

### Python Data Logger

```python
import paho.mqtt.client as mqtt
import json
import csv
from datetime import datetime

class FermentationLogger:
    def __init__(self, batch_id):
        self.batch_id = batch_id
        self.csv_file = f"{batch_id}_log.csv"

        # Initialize CSV
        with open(self.csv_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['timestamp', 'type', 'value', 'unit'])

    def log_data(self, data_type, value, unit):
        with open(self.csv_file, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                datetime.now().isoformat(),
                data_type,
                value,
                unit
            ])

    def on_message(self, client, userdata, msg):
        data = json.loads(msg.payload.decode())

        if 'bubbles' in msg.topic:
            self.log_data('bubble_rate', data.get('rate', 0), 'bubbles/min')

        elif 'gravity' in msg.topic:
            self.log_data('gravity', data['gravity'], 'SG')

        elif 'temperature' in msg.topic:
            self.log_data('temperature', data['temperature'], data['units'])

# Usage
logger = FermentationLogger('batch1')

client = mqtt.Client()
client.username_pw_set("tipsylab", "password")
client.on_message = logger.on_message

client.connect("localhost", 1883, 60)
client.subscribe(f"tipsylab/{logger.batch_id}/#")
client.loop_forever()
```

### Node-RED Dashboard

Complete flow for creating a fermentation dashboard in Node-RED - see [examples/mqtt_examples/nodered_dashboard.json](../examples/mqtt_examples/nodered_dashboard.json)

---

## Best Practices

### Message Design

1. **Use JSON**: Structured, parseable, human-readable
2. **Include Timestamps**: Always include message creation time
3. **Keep Messages Small**: < 1KB for efficiency
4. **Use Consistent Units**: Document and stick to units
5. **Include Sensor ID**: Identify source of data

### Topic Design

1. **Hierarchical**: General to specific
2. **Descriptive**: Self-documenting topic names
3. **Consistent**: Follow naming convention
4. **Avoid Deep Nesting**: 3-4 levels maximum

### Publishing

1. **QoS 1**: Use for important data (at-least-once delivery)
2. **Retained Messages**: Use for state data
3. **Throttle Updates**: Don't spam broker (reasonable intervals)
4. **Handle Reconnects**: Implement automatic reconnection
5. **Validate Data**: Check values before publishing

### Subscribing

1. **Use Wildcards Wisely**: `+` for single level, `#` for multiple
2. **Filter Client-Side**: Don't subscribe to unnecessary topics
3. **Handle Errors**: Gracefully handle malformed messages
4. **Process Asynchronously**: Don't block message handler

### Security

1. **Use Authentication**: Always set username/password
2. **Use TLS**: Enable encryption for remote connections
3. **Limit Access**: Use ACLs to restrict topic access
4. **Secure Credentials**: Don't hardcode passwords
5. **Isolate Network**: Consider separate VLAN for IoT devices

### Reliability

1. **Last Will & Testament**: Set will message for unexpected disconnects
2. **Keep-Alive**: Set appropriate interval (60s recommended)
3. **Clean Session**: Use clean_session=False for persistent subscriptions
4. **Message Persistence**: Enable broker message persistence
5. **Monitor Connection**: Implement connection health checks

---

## Testing

### Command-Line Testing

```bash
# Subscribe to all topics
mosquitto_sub -h localhost -u tipsylab -P password -t 'tipsylab/#' -v

# Publish test bubble
mosquitto_pub -h localhost -u tipsylab -P password \
  -t 'tipsylab/batch1/bubbles' \
  -m '{"count":1,"timestamp":1699999999000,"rate":45.0}'

# Publish test gravity
mosquitto_pub -h localhost -u tipsylab -P password \
  -t 'tipsylab/batch1/gravity' \
  -m '{"gravity":1.042,"temperature":20.5,"temp_units":"C","timestamp":1699999999000}'

# Retain flag (-r)
mosquitto_pub -h localhost -u tipsylab -P password \
  -t 'tipsylab/batch1/temperature' \
  -m '{"temperature":20.5,"units":"C","timestamp":1699999999000}' \
  -r
```

### MQTT Explorer

Use [MQTT Explorer](http://mqtt-explorer.com/) for visual debugging:
- View topic hierarchy
- Monitor messages in real-time
- Publish test messages
- View retained messages
- Analyze message frequency

---

## Troubleshooting

**Messages not received:**
- Check broker is running
- Verify credentials
- Check topic spelling
- Ensure subscriber is connected
- Check QoS settings

**Delayed messages:**
- Check network latency
- Verify broker resources
- Check for message queue buildup
- Monitor broker logs

**Missing data:**
- Check retained flag
- Verify QoS level
- Check for clean_session setting
- Monitor client disconnects

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for more details.

---

## Additional Resources

- [MQTT Specification](https://mqtt.org/mqtt-specification/)
- [Paho MQTT Python](https://github.com/eclipse/paho.mqtt.python)
- [PubSubClient Arduino](https://github.com/knolleary/pubsubclient)
- [Mosquitto Documentation](https://mosquitto.org/documentation/)
- [Home Assistant MQTT](https://www.home-assistant.io/integrations/mqtt/)
