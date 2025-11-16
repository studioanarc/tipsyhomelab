# MQTT Integration and Sensor Management System

A comprehensive, extensible sensor management system for wine production monitoring with MQTT integration, automatic sensor discovery, and persistent data storage.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Components](#components)
- [Sensor Types](#sensor-types)
- [Message Formats](#message-formats)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)
- [Extending the System](#extending-the-system)
- [API Reference](#api-reference)

## 🎯 Overview

This system provides a complete solution for monitoring wine production through various sensors:

- **MQTT Integration**: Robust MQTT client with auto-reconnect and offline buffering
- **Dynamic Sensor Discovery**: Automatically detect and register sensors from MQTT topics
- **Extensible Architecture**: Easy to add new sensor types
- **Health Monitoring**: Track sensor status, data quality, and system health
- **Persistent Storage**: SQLite-based time-series data storage with indexing
- **Alert System**: Configurable alerts based on sensor readings

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                 MQTT Broker                          │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│              MQTT Handler                            │
│  • Auto-reconnect with exponential backoff          │
│  • Message buffering for offline resilience         │
│  • Topic subscription management                    │
└─────────────────┬───────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────┐
│           Sensor Registry                            │
│  • Dynamic sensor discovery                         │
│  • Topic routing to sensors                         │
│  • Health monitoring                                │
│  • Capability aggregation                           │
└─────────────────┬───────────────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
┌────────▼──────┐  ┌──────▼─────────────────┐
│  Base Sensor  │  │   Data Manager         │
│  (Abstract)   │  │  • SQLite storage      │
└────────┬──────┘  │  • Data aggregation    │
         │         │  • Export functions    │
    ┌────┴────┐    │  • Retention policies  │
    │         │    └────────────────────────┘
┌───▼──┐  ┌──▼───┐
│Bubble│  │iSpindel│  [Other Sensors...]
│Sensor│  │Sensor │
└──────┘  └───────┘
```

## 📦 Components

### 1. MQTT Handler (`mqtt_handler.py`)

Manages all MQTT communication with features:

- **Auto-reconnect**: Exponential backoff retry strategy
- **Message Buffering**: Queue messages when offline (configurable buffer size)
- **Thread-safe**: Safe for concurrent operations
- **Health Monitoring**: Connection statistics and state tracking

### 2. Sensor Registry (`sensors/sensor_registry.py`)

Central sensor management system:

- **Auto-discovery**: Detect sensors from MQTT topic patterns
- **Dynamic Registration**: Add/remove sensors at runtime
- **Topic Routing**: Efficiently route messages to appropriate sensors
- **Health Checks**: Monitor sensor status and data quality
- **Capability Aggregation**: Unified view of all sensor capabilities

### 3. Base Sensor (`sensors/base_sensor.py`)

Abstract base class for all sensors providing:

- **Standard Interface**: Consistent API across sensor types
- **Health Monitoring**: Track last seen, message counts, error rates
- **Data Validation**: Quality assessment of sensor readings
- **Capability Declaration**: Self-describing sensors

### 4. Data Manager (`data_manager.py`)

Persistent storage and data management:

- **Time-series Storage**: Efficient SQLite schema with proper indexing
- **Data Aggregation**: Hourly/daily summaries for long-term analysis
- **Retention Policies**: Automatic cleanup of old data
- **Export Functions**: JSON/CSV export capabilities
- **Thread-safe**: Concurrent access support

## 🔌 Sensor Types

### Required Sensors

#### Bubble Counter (`bubble_sensor.py`)
Monitors CO2 bubble production during fermentation.

**Capabilities:**
- Bubble count (incremental or cumulative)
- Bubble rate (bubbles per minute)
- Optional: temperature, battery

**Status:** REQUIRED for fermentation monitoring

### Optional Sensors

#### iSpindel (`ispindel_sensor.py`)
Wireless hydrometer for gravity and temperature.

**Capabilities:**
- Specific gravity
- Temperature
- Tilt angle
- Battery voltage
- RSSI (signal strength)

**Features:**
- Calibration polynomial support
- Battery percentage estimation
- Fermentation stage detection

#### pH Sensor (`optional_sensors.py`)
Monitors wine acidity.

**Range:** 0-14 pH (typical wine: 3.0-4.0)

#### Dissolved Oxygen Sensor
Tracks oxidation risk.

**Range:** 0-20 mg/L (ideal wine: 0-2 mg/L)

#### Pressure Sensor
Monitors fermentation vessel pressure.

#### Temperature Sensor
Standalone temperature monitoring.

#### Humidity Sensor
Environmental humidity tracking.

#### Generic Sensor
Flexible sensor for any single numeric value.

## 📨 Message Formats

### Bubble Counter

```json
{
  "timestamp": "2025-11-16T10:30:00Z",
  "bubbles": 42,
  "interval": 60,
  "rate": 0.7,
  "temperature": 22.5,
  "battery": 85,
  "cumulative": true
}
```

**MQTT Topics:**
- `sensors/bubble/{sensor_id}`
- `sensors/bubble/{sensor_id}/#`
- `homeassistant/sensor/bubble/{sensor_id}/state`

### iSpindel

```json
{
  "name": "iSpindel000",
  "ID": 123456,
  "angle": 45.67,
  "temperature": 20.5,
  "temp_units": "C",
  "battery": 3.8,
  "gravity": 1.050,
  "interval": 900,
  "RSSI": -65
}
```

**MQTT Topics:**
- `ispindel/{sensor_id}`
- `sensors/ispindel/{sensor_id}`

### pH Sensor

```json
{
  "timestamp": "2025-11-16T10:30:00Z",
  "ph": 3.5,
  "temperature": 20.0
}
```

**MQTT Topics:**
- `sensors/ph/{sensor_id}`

### Generic Sensor

```json
{
  "timestamp": "2025-11-16T10:30:00Z",
  "value": 42.5,
  "unit": "unit_name"
}
```

## 🚀 Installation

1. **Install Dependencies**

```bash
cd /home/user/tipsyhomelab/addon/rootfs/app
pip install -r requirements.txt
```

2. **Configure MQTT Broker**

Ensure you have an MQTT broker running (e.g., Mosquitto):

```bash
# Install Mosquitto (if not already installed)
apt-get install mosquitto mosquitto-clients

# Start broker
systemctl start mosquitto
```

3. **Set Up Database Directory**

```bash
mkdir -p /data
```

## 📖 Usage

### Basic Integration

```python
from mqtt_handler import MQTTHandler
from sensors import SensorRegistry
from data_manager import DataManager

# Configure MQTT
mqtt_config = {
    'broker': 'localhost',
    'port': 1883,
    'username': None,
    'password': None,
}

# Initialize components
mqtt = MQTTHandler(mqtt_config)
registry = SensorRegistry({'auto_discovery': True})
data_mgr = DataManager('/data/wine_monitor.db')

# Connect callback
def handle_message(topic, payload):
    sensor_data = registry.process_message(topic, payload)
    if sensor_data:
        data_mgr.store_sensor_data(sensor_data)

# Set up and connect
mqtt.add_message_callback(handle_message)
mqtt.connect()
mqtt.subscribe_multiple(registry.get_all_topics())
```

### Running the Example System

```python
python example_integration.py
```

### Manual Sensor Registration

```python
# Pre-configure specific sensors
registry = SensorRegistry({
    'sensors': {
        'bubble_001': {
            'type': 'bubble',
            'timeout_seconds': 300,
            'cumulative_mode': True,
        },
        'ispindel_001': {
            'type': 'ispindel',
            'timeout_seconds': 1800,
            'polynomial': [1.0, -0.001, 0.0001],  # Calibration
        },
    }
})
```

### Querying Data

```python
from datetime import datetime, timedelta

# Get recent sensor data
data = data_mgr.get_sensor_data(
    sensor_id='bubble_001',
    start_time=datetime.now() - timedelta(hours=24),
    limit=100
)

# Get time series for a measurement
time_series = data_mgr.get_time_series(
    sensor_id='bubble_001',
    measurement_name='bubble_rate',
    start_time=datetime.now() - timedelta(days=7)
)

# Get aggregated data
aggregated = data_mgr.get_aggregated_data(
    sensor_id='bubble_001',
    measurement_name='bubble_rate',
    start_time=datetime.now() - timedelta(days=30),
    period_type='hourly'
)
```

### Health Monitoring

```python
# Check sensor health
health = registry.get_health_summary()
print(f"Online sensors: {health['online']}/{health['total_sensors']}")
print(f"Required sensors online: {health['required_online']}")

# Check specific sensor
sensor = registry.get_sensor('bubble_001')
if sensor:
    report = sensor.get_health_report()
    print(f"Status: {report['status']}")
    print(f"Last seen: {report['last_seen']}")
    print(f"Error rate: {report['error_rate']:.2%}")
```

## ⚙️ Configuration

### MQTT Configuration

```python
mqtt_config = {
    'broker': 'localhost',           # MQTT broker address
    'port': 1883,                     # MQTT port
    'username': None,                 # Optional username
    'password': None,                 # Optional password
    'client_id': 'wine_monitor',     # Client identifier
    'keepalive': 60,                  # Keep-alive interval (seconds)
    'qos': 1,                         # Quality of Service (0, 1, 2)
    'retain': False,                  # Retain published messages
    'buffer_size': 1000,              # Offline message buffer size
    'reconnect_delay': 5,             # Initial reconnect delay (seconds)
    'reconnect_max_delay': 300,       # Max reconnect delay (seconds)
    'reconnect_exponential_backoff': True,
}
```

### Sensor Registry Configuration

```python
registry_config = {
    'auto_discovery': True,           # Enable automatic sensor discovery
    'auto_register': True,            # Auto-register discovered sensors
    'discovery_timeout': 300,         # Discovery timeout (seconds)
    'sensors': {                      # Pre-configured sensors
        'sensor_id': {
            'type': 'bubble',         # Sensor type
            'timeout_seconds': 300,   # Sensor timeout
            # ... sensor-specific config
        }
    }
}
```

### Data Manager Configuration

```python
data_config = {
    'raw_retention_days': 90,         # Keep raw data for 90 days
    'aggregated_retention_days': 365, # Keep aggregated data for 1 year
    'auto_aggregate': True,           # Enable automatic aggregation
    'aggregation_interval_minutes': 60,
}
```

## 🔧 Extending the System

### Creating a Custom Sensor

1. **Create sensor class** inheriting from `BaseSensor`:

```python
from sensors.base_sensor import BaseSensor, DataQuality

class MyCustomSensor(BaseSensor):
    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'my_sensor',
            'required': False,
            'measurements': ['my_measurement'],
            'units': {'my_measurement': 'my_unit'},
            'update_interval': 60,
            'description': 'My custom sensor',
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Parse the incoming message
        value = float(payload['value'])

        return {
            'timestamp': datetime.now().isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'my_sensor',
            'measurements': {'my_measurement': value},
            'metadata': {},
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        # Validate the parsed data
        measurements = data['measurements']
        value = measurements['my_measurement']

        if value < 0 or value > 100:
            return False, DataQuality.INVALID, "Value out of range"

        return True, DataQuality.GOOD, None
```

2. **Register in sensor registry**:

```python
# In sensor_registry.py
from .my_custom_sensor import MyCustomSensor

SENSOR_CLASSES = {
    # ... existing sensors
    'my_sensor': MyCustomSensor,
}

TOPIC_PATTERNS = {
    # ... existing patterns
    'my_sensor': [
        re.compile(r'^sensors?/my_sensor/([^/]+)'),
    ],
}
```

### Adding Custom Alerts

```python
def check_custom_alert(self, sensor_data: dict):
    """Custom alert logic."""
    measurements = sensor_data['measurements']

    if 'my_measurement' in measurements:
        value = measurements['my_measurement']

        if value > 80:
            self.create_alert(
                alert_type='high_value',
                severity='warning',
                sensor_id=sensor_data['sensor_id'],
                message=f"High value detected: {value}",
                details={'value': value}
            )
```

## 📚 API Reference

### MQTTHandler

```python
# Connection
mqtt.connect(blocking=False) -> bool
mqtt.disconnect()
mqtt.is_connected() -> bool
mqtt.wait_for_connection(timeout=None) -> bool

# Subscriptions
mqtt.subscribe(topic, qos=1, callback=None)
mqtt.subscribe_multiple(topics, qos=1)

# Publishing
mqtt.publish(topic, payload, qos=1, retain=False) -> bool
mqtt.publish_sensor_data(sensor_id, data) -> bool
mqtt.publish_prediction(prediction) -> bool
mqtt.publish_alert(alert) -> bool
mqtt.publish_health(health) -> bool

# Callbacks
mqtt.add_message_callback(callback)

# Statistics
mqtt.get_statistics() -> dict
```

### SensorRegistry

```python
# Sensor management
registry.register_sensor(sensor_id, sensor_type, config) -> BaseSensor
registry.unregister_sensor(sensor_id) -> bool
registry.get_sensor(sensor_id) -> BaseSensor
registry.get_all_sensors() -> Dict[str, BaseSensor]
registry.get_sensors_by_type(sensor_type) -> List[BaseSensor]

# Message processing
registry.process_message(topic, payload) -> Optional[dict]

# Health monitoring
registry.get_health_summary() -> dict
registry.check_required_sensors() -> tuple[bool, List[str]]
registry.get_capabilities_summary() -> dict

# Topics
registry.get_all_topics() -> List[str]

# Maintenance
registry.cleanup_stale_sensors(timeout_hours=24)
```

### DataManager

```python
# Storage
data_mgr.store_sensor_data(data) -> bool
data_mgr.store_prediction(prediction) -> bool
data_mgr.store_alert(alert) -> bool

# Retrieval
data_mgr.get_sensor_data(sensor_id, start_time, end_time, ...) -> List[dict]
data_mgr.get_latest_value(sensor_id, measurement_name) -> Optional[tuple]
data_mgr.get_time_series(sensor_id, measurement_name, start_time, end_time) -> List[tuple]
data_mgr.get_aggregated_data(sensor_id, measurement_name, ...) -> List[dict]

# Aggregation
data_mgr.aggregate_data(start_time, end_time, period_type) -> bool

# Maintenance
data_mgr.cleanup_old_data()
data_mgr.export_data(output_path, format='json') -> bool
data_mgr.get_statistics() -> dict
```

### BaseSensor

```python
# Core methods (must implement)
sensor.get_capabilities() -> dict
sensor.parse_message(payload) -> dict
sensor.validate_data(data) -> tuple[bool, DataQuality, Optional[str]]

# Health monitoring
sensor.update_health(success=True, quality=None)
sensor.get_health_report() -> dict

# Message processing
sensor.process_message(topic, payload) -> Optional[dict]

# Utilities
sensor.get_mqtt_topics() -> List[str]
sensor.is_required() -> bool
sensor.to_dict() -> dict
```

## 🔍 Testing

### Simulate Sensor Data

```python
# Test bubble counter
test_payload = {
    "timestamp": "2025-11-16T10:30:00Z",
    "bubbles": 42,
    "rate": 0.7,
}
mqtt.publish('sensors/bubble/test_001', test_payload)

# Test iSpindel
test_payload = {
    "name": "test_ispindel",
    "angle": 45.0,
    "temperature": 20.5,
    "battery": 3.8,
    "gravity": 1.050,
}
mqtt.publish('ispindel/test_ispindel', test_payload)
```

## 📝 License

Part of the TipsyHomeLab wine production monitoring system.

## 🤝 Contributing

When adding new sensors:

1. Inherit from `BaseSensor`
2. Implement all abstract methods
3. Add comprehensive validation
4. Include unit tests
5. Document message format
6. Update this README

## 📧 Support

For issues or questions, check the main project documentation or create an issue in the repository.
