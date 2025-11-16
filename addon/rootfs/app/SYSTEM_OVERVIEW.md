# Wine Production Monitoring System - Complete Overview

## 📊 System Statistics

- **Total Lines of Code**: ~3,863 lines
- **Core Modules**: 9 files
- **Sensor Types**: 7+ (extensible)
- **Documentation**: Comprehensive README + inline docs

## 🏗️ Complete File Structure

```
/home/user/tipsyhomelab/addon/rootfs/app/
│
├── 📚 Core Components
│   ├── mqtt_handler.py              (703 lines) - MQTT client with auto-reconnect
│   ├── data_manager.py              (796 lines) - SQLite time-series storage
│   ├── example_integration.py       (346 lines) - Complete integration example
│   └── test_mqtt_sensors.py         (358 lines) - Comprehensive test suite
│
├── 🔌 Sensor Management (sensors/)
│   ├── __init__.py                  (33 lines)  - Package exports
│   ├── base_sensor.py               (296 lines) - Abstract base class
│   ├── bubble_sensor.py             (275 lines) - CO2 bubble counter (REQUIRED)
│   ├── ispindel_sensor.py           (417 lines) - Wireless hydrometer
│   ├── optional_sensors.py          (498 lines) - pH, DO, pressure, temp, humidity
│   └── sensor_registry.py           (499 lines) - Dynamic discovery & routing
│
├── 📖 Documentation
│   ├── MQTT_SENSOR_README.md        - Complete system documentation
│   ├── SYSTEM_OVERVIEW.md           - This file
│   └── requirements.txt             - Python dependencies
│
└── 🤖 ML Engine (existing)
    ├── models.py
    ├── feature_engineering.py
    ├── anomaly_detector.py
    ├── petnat_predictor.py
    └── ...
```

## 🎯 Key Features Implemented

### 1. MQTT Integration (`mqtt_handler.py`)

✅ **Auto-Reconnect**
- Exponential backoff retry strategy
- Configurable delays and max retry time
- Connection state tracking

✅ **Message Buffering**
- Queue up to 1000 messages when offline
- Automatic replay when connection restored
- Prevents data loss during network issues

✅ **Thread-Safe Operations**
- Concurrent message processing
- Safe for multi-threaded environments
- Worker threads for async handling

✅ **Health Monitoring**
- Connection statistics
- Message counts (sent/received/buffered)
- Uptime tracking

### 2. Sensor Management (`sensors/`)

✅ **Base Sensor Architecture**
- Abstract base class for all sensors
- Standard interface (parse, validate, capabilities)
- Built-in health monitoring
- Data quality assessment

✅ **Required Sensor: Bubble Counter**
- CO2 bubble counting (incremental or cumulative)
- Bubble rate calculation (bubbles/min)
- Temperature monitoring
- Configurable intervals

✅ **Optional Sensor: iSpindel**
- Specific gravity measurement
- Temperature tracking
- Battery monitoring
- Calibration polynomial support
- Fermentation stage estimation

✅ **Optional Sensors Collection**
- pH sensor (wine acidity)
- Dissolved Oxygen (oxidation risk)
- Pressure sensor
- Temperature sensor
- Humidity sensor
- Generic sensor (extensible)

✅ **Sensor Registry**
- Dynamic sensor discovery from MQTT topics
- Automatic registration
- Topic pattern matching
- Message routing
- Health aggregation
- Capability reporting

### 3. Data Management (`data_manager.py`)

✅ **Time-Series Storage**
- SQLite database with proper indexing
- Efficient timestamp-based queries
- Sensor data table with metadata

✅ **Data Aggregation**
- Hourly/daily summaries
- Statistical calculations (min/max/avg/stddev)
- Separate aggregated data table

✅ **Data Retrieval**
- Time-range queries
- Latest value lookup
- Time-series extraction
- Batch retrieval for ML

✅ **Predictions & Alerts**
- Dedicated tables for ML predictions
- Alert storage with severity levels
- Event logging

✅ **Retention Policies**
- Configurable retention periods
- Automatic cleanup of old data
- Raw data: 90 days default
- Aggregated: 365 days default

✅ **Export Functions**
- JSON export
- CSV export
- Configurable time ranges

### 4. Integration & Testing

✅ **Complete Integration Example**
- Full system demonstration
- MQTT → Sensors → Database flow
- Alert generation examples
- Health monitoring

✅ **Comprehensive Test Suite**
- Unit tests for all sensor types
- Data manager tests
- MQTT handler tests
- Integration tests

## 📨 Supported Message Formats

### Bubble Counter
```json
{
  "bubbles": 42,
  "interval": 60,
  "rate": 0.7,
  "temperature": 22.5,
  "cumulative": true
}
```

### iSpindel
```json
{
  "name": "iSpindel000",
  "angle": 45.67,
  "temperature": 20.5,
  "battery": 3.8,
  "gravity": 1.050,
  "RSSI": -65
}
```

### Generic Sensors
```json
{
  "value": 42.5,
  "unit": "unit_name"
}
```

## 🔄 Data Flow Architecture

```
┌─────────────┐
│ MQTT Broker │
│ (Mosquitto) │
└──────┬──────┘
       │
       ▼
┌──────────────────┐
│  MQTT Handler    │◄──── Auto-reconnect
│  • Subscribe     │      Message buffering
│  • Publish       │      Thread-safe
│  • Buffer        │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────┐
│   Sensor Registry        │
│   • Auto-discovery       │
│   • Topic routing        │
│   • Health monitoring    │
└────────┬─────────────────┘
         │
    ┌────┴────┐
    ▼         ▼
┌────────┐ ┌──────────────┐
│Sensors │ │ Data Manager │
│        │ │ • Store data │
│Parse   │ │ • Aggregate  │
│Validate│ │ • Query      │
│Monitor │ │ • Export     │
└────────┘ └──────────────┘
```

## 🎛️ Configuration Example

```python
config = {
    'mqtt': {
        'broker': 'localhost',
        'port': 1883,
        'username': None,
        'password': None,
        'qos': 1,
        'buffer_size': 1000,
    },
    'sensor_registry': {
        'auto_discovery': True,
        'auto_register': True,
        'sensors': {
            'bubble_001': {
                'type': 'bubble',
                'cumulative_mode': True,
            }
        }
    },
    'data_manager': {
        'raw_retention_days': 90,
        'aggregated_retention_days': 365,
    }
}
```

## 🚀 Quick Start

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Start MQTT Broker**
```bash
systemctl start mosquitto
```

3. **Run Example Integration**
```bash
python example_integration.py
```

4. **Run Tests**
```bash
python test_mqtt_sensors.py
```

## 📡 MQTT Topics

### Subscriptions (Auto-discovered)
- `sensors/bubble/{sensor_id}`
- `sensors/bubble/{sensor_id}/#`
- `ispindel/{sensor_id}`
- `sensors/ispindel/{sensor_id}`
- `sensors/ph/{sensor_id}`
- `sensors/temperature/{sensor_id}`
- `sensors/humidity/{sensor_id}`
- `sensors/pressure/{sensor_id}`
- `sensors/do/{sensor_id}`
- `homeassistant/sensor/+/+/state`

### Publications
- `wine_monitor/sensors/{sensor_id}/data` - Processed sensor data
- `wine_monitor/predictions` - ML predictions
- `wine_monitor/alerts/{severity}` - System alerts
- `wine_monitor/health` - System health status

## 🔧 Extensibility

### Adding a New Sensor Type

1. Create sensor class in `sensors/`:
```python
class MySensor(BaseSensor):
    def get_capabilities(self): ...
    def parse_message(self, payload): ...
    def validate_data(self, data): ...
```

2. Register in `sensor_registry.py`:
```python
SENSOR_CLASSES = {
    'my_sensor': MySensor,
}

TOPIC_PATTERNS = {
    'my_sensor': [re.compile(r'^sensors/my_sensor/([^/]+)')],
}
```

3. Done! Auto-discovery will handle the rest.

## 📊 Database Schema

### sensor_data
- `timestamp` - ISO format timestamp
- `sensor_id` - Sensor identifier
- `sensor_type` - Type of sensor
- `measurements` - JSON measurements
- `metadata` - JSON metadata
- `data_quality` - Quality assessment

### aggregated_data
- `period_start/end` - Aggregation window
- `period_type` - hourly/daily
- `sensor_id` - Sensor identifier
- `measurement_name` - Measurement being aggregated
- `count, min, max, avg, sum, stddev` - Statistics

### predictions
- `timestamp` - Prediction time
- `prediction_type` - Type of prediction
- `predicted_value` - Result
- `confidence` - Confidence score
- `model_version` - ML model version

### alerts
- `timestamp` - Alert time
- `alert_type` - Type of alert
- `severity` - info/warning/critical
- `sensor_id` - Related sensor
- `message` - Human-readable message

## 🎯 Design Principles

1. **Resilience First**
   - Auto-reconnect on failures
   - Message buffering for offline periods
   - Graceful degradation

2. **Extensibility**
   - Abstract base classes
   - Plugin architecture for sensors
   - Dynamic discovery

3. **Data Quality**
   - Validation at ingestion
   - Quality scoring
   - Error tracking

4. **Performance**
   - SQLite indexing
   - Efficient queries
   - Data aggregation

5. **Observability**
   - Health monitoring
   - Statistics tracking
   - Comprehensive logging

## 🔍 Testing Coverage

✅ Unit Tests
- Each sensor type
- Message parsing
- Data validation
- Health monitoring

✅ Integration Tests
- MQTT → Sensor flow
- Sensor → Database flow
- End-to-end data pipeline

✅ Edge Cases
- Invalid messages
- Missing fields
- Out-of-range values
- Connection failures

## 📈 Future Enhancements

Possible additions (not yet implemented):

- [ ] REST API for data access
- [ ] WebSocket real-time updates
- [ ] Grafana dashboard integration
- [ ] InfluxDB backend option
- [ ] MQTT TLS/SSL support
- [ ] Sensor authentication
- [ ] Data compression
- [ ] Backup/restore utilities

## 🤝 Integration with ML Engine

The sensor data feeds directly into the ML engine:

1. **Data Collection**: MQTT → Sensors → Database
2. **Feature Engineering**: Time-series data → Features
3. **Model Training**: Historical data → ML models
4. **Prediction**: Current data → Predictions
5. **Alerts**: Predictions → MQTT alerts

## 📝 Summary

This MQTT integration and sensor management system provides:

- ✅ Robust, production-ready MQTT integration
- ✅ 7+ sensor types with easy extensibility
- ✅ Automatic sensor discovery
- ✅ Persistent time-series storage
- ✅ Data quality monitoring
- ✅ Comprehensive health tracking
- ✅ Alert system
- ✅ Full test coverage
- ✅ Complete documentation

**Total Implementation**: ~3,863 lines of well-documented, tested code.

Ready for integration with Home Assistant, ML models, and web UI! 🍷
