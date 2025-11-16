# Wine Fermentation Monitor - Documentation

## Overview

The Wine Fermentation Monitor is an advanced Home Assistant add-on that provides real-time monitoring, machine learning predictions, and intelligent alerting for wine fermentation processes.

## Quick Start

1. **Install the Add-on**
   - Navigate to Supervisor → Add-on Store
   - Find "Wine Fermentation Monitor"
   - Click Install

2. **Configure MQTT**
   ```yaml
   mqtt:
     host: core-mosquitto
     port: 1883
     username: your_mqtt_user
     password: your_mqtt_password
   ```

3. **Enable Sensors**
   Configure which sensors you want to monitor:
   ```yaml
   sensors:
     temperature:
       enabled: true
       topic: wine/sensors/temperature
     specific_gravity:
       enabled: true
       topic: wine/sensors/sg
   ```

4. **Start the Add-on**
   - Click "Start"
   - Monitor the logs for successful startup
   - Check health endpoint: `http://YOUR_HA_IP:8099/health`

## Configuration Reference

### MQTT Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `host` | string | `core-mosquitto` | MQTT broker hostname |
| `port` | integer | `1883` | MQTT broker port |
| `username` | string | `""` | MQTT username (optional) |
| `password` | string | `""` | MQTT password (optional) |
| `discovery_prefix` | string | `homeassistant` | HA discovery prefix |
| `base_topic` | string | `wine/fermentation` | Base topic for published data |

### Sensor Configuration

Each sensor can be individually configured:

```yaml
sensors:
  temperature:
    enabled: true                    # Enable/disable sensor
    topic: wine/sensors/temperature  # MQTT topic to subscribe
    device_class: temperature        # HA device class
    unit: "°C"                       # Unit of measurement
```

**Available Sensors:**
- `temperature` - Fermentation temperature
- `specific_gravity` - Wort/must specific gravity
- `ph` - Acidity level
- `pressure` - Fermentation pressure (optional)

### Machine Learning Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable ML predictions |
| `prediction_interval` | integer | `3600` | Prediction interval (seconds) |
| `model_retrain_days` | integer | `7` | Model retraining frequency (days) |
| `min_samples_for_training` | integer | `100` | Minimum samples before training |

### Alert Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable alerts |
| `temperature_min` | float | `18.0` | Minimum safe temperature (°C) |
| `temperature_max` | float | `28.0` | Maximum safe temperature (°C) |
| `sg_stuck_threshold` | float | `0.001` | SG change threshold for stuck detection |
| `sg_stuck_hours` | integer | `48` | Hours without change to trigger alert |
| `ph_min` | float | `2.8` | Minimum safe pH |
| `ph_max` | float | `4.0` | Maximum safe pH |

### Logging Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `INFO` | Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `structured` | boolean | `true` | Use JSON structured logging |

## MQTT Topics

### Subscribe Topics (Your Sensors → Add-on)

The add-on subscribes to these topics to receive sensor data:

- `wine/sensors/temperature` - Temperature readings
  ```json
  {"value": 22.5, "unit": "°C", "timestamp": "2025-11-16T10:30:00Z"}
  ```

- `wine/sensors/sg` - Specific gravity readings
  ```json
  {"value": 1.045, "unit": "SG", "timestamp": "2025-11-16T10:30:00Z"}
  ```

- `wine/sensors/ph` - pH readings
  ```json
  {"value": 3.4, "unit": "pH", "timestamp": "2025-11-16T10:30:00Z"}
  ```

### Publish Topics (Add-on → Home Assistant)

The add-on publishes to these topics:

- `wine/fermentation/status` - Current fermentation status
- `wine/fermentation/prediction` - ML predictions
- `wine/fermentation/alerts` - Alert notifications
- `homeassistant/sensor/wine_monitor/*/config` - MQTT Discovery messages

## Home Assistant Integration

### Automatic Discovery

The add-on automatically creates Home Assistant entities via MQTT discovery:

- `sensor.wine_temperature` - Current temperature
- `sensor.wine_specific_gravity` - Current SG
- `sensor.wine_ph` - Current pH
- `sensor.wine_fermentation_status` - Fermentation stage
- `sensor.wine_completion_prediction` - Predicted completion time

### Manual Entity Configuration

If discovery doesn't work, add entities manually:

```yaml
mqtt:
  sensor:
    - name: "Wine Temperature"
      state_topic: "wine/sensors/temperature"
      value_template: "{{ value_json.value }}"
      unit_of_measurement: "°C"
      device_class: temperature
```

## Automation Examples

### Temperature Alert

```yaml
automation:
  - alias: "Wine Temperature Too High"
    trigger:
      - platform: mqtt
        topic: wine/fermentation/alerts
        payload: temperature_high
    action:
      - service: notify.mobile_app
        data:
          message: "Wine fermentation temperature is too high!"
```

### Fermentation Complete Notification

```yaml
automation:
  - alias: "Wine Fermentation Complete"
    trigger:
      - platform: state
        entity_id: sensor.wine_fermentation_status
        to: "complete"
    action:
      - service: notify.mobile_app
        data:
          message: "Your wine fermentation is complete!"
```

## Monitoring

### Health Checks

Access health endpoints directly:

- **Health**: `http://YOUR_HA_IP:8099/health`
  ```json
  {
    "status": "healthy",
    "timestamp": "2025-11-16T10:30:00Z",
    "details": {
      "mqtt_connected": true,
      "uptime_seconds": 3600
    }
  }
  ```

- **Metrics**: `http://YOUR_HA_IP:8099/metrics`
  ```
  wine_monitor_up{service="wine_fermentation_monitor"} 1
  wine_monitor_uptime_seconds{service="wine_fermentation_monitor"} 3600
  ```

### Logs

View logs in Home Assistant:
1. Supervisor → Wine Fermentation Monitor
2. Click "Logs" tab
3. Set log level in configuration for more detail

## Troubleshooting

### Add-on Won't Start

**Check MQTT Connection:**
1. Verify Mosquitto broker is running
2. Check MQTT credentials
3. Test with MQTT Explorer

**Check Logs:**
```bash
docker logs addon_wine_fermentation_monitor
```

### No Sensor Data

**Verify MQTT Topics:**
1. Confirm sensors are publishing to correct topics
2. Use MQTT Explorer to monitor messages
3. Enable DEBUG logging to see received messages

**Check Configuration:**
```yaml
sensors:
  temperature:
    enabled: true  # Must be true
    topic: wine/sensors/temperature  # Must match sensor
```

### ML Predictions Not Working

**Requirements:**
- Minimum 100 sensor readings (configurable)
- Consistent data over time
- ML enabled in configuration

**Check Status:**
- View logs for model training messages
- Verify `/data/models/` directory has model files

## Data Storage

The add-on stores data in these directories:

- `/data/models/` - Trained ML models (persistent)
- `/data/history/` - Historical sensor data (persistent)
- `/data/logs/` - Application logs (persistent)

**Backup Recommendation:** Include `/data/` in your Home Assistant backups.

## Performance

### Resource Usage

Typical resource consumption:
- **Memory**: ~150-200 MB
- **CPU**: <5% (idle), 10-20% (during ML training)
- **Disk**: ~50 MB + historical data

### Optimization

For better performance:
1. Increase `prediction_interval` if CPU usage is high
2. Reduce `min_samples_for_training` for faster initial predictions
3. Disable ML if not needed: `ml.enabled: false`

## Security

### Best Practices

1. **Use Authentication**: Enable MQTT username/password
2. **Secure Credentials**: Use Home Assistant secrets
3. **Network Isolation**: Keep MQTT on internal network
4. **Regular Updates**: Update add-on when new versions available

### Credential Management

Use Home Assistant secrets:

```yaml
mqtt:
  username: !secret mqtt_username
  password: !secret mqtt_password
```

## Advanced Configuration

### Custom Model Parameters

```yaml
ml:
  model_type: random_forest  # or gradient_boosting, linear_regression
  enable_anomaly_detection: true
  anomaly_threshold: 2.5
  prediction_window_hours: 72
  feature_window_hours: 24
```

### Alert Cooldown

Prevent alert spam:

```yaml
alerts:
  notification_cooldown: 3600  # Seconds between same alert
```

## Support

- **GitHub Issues**: https://github.com/tipsyhomelab/wine-fermentation-monitor/issues
- **Documentation**: https://github.com/tipsyhomelab/wine-fermentation-monitor/wiki
- **Community Forum**: https://community.home-assistant.io/

## License

MIT License - See LICENSE file for details
