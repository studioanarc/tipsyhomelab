# Wine Fermentation Monitor Add-on

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Architecture](https://img.shields.io/badge/architecture-multi--arch-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

Advanced wine fermentation monitoring system with ML-powered predictions and intelligent alerting.

## Features

- **Real-time Monitoring**: Track temperature, specific gravity, pH, and pressure
- **ML Predictions**: Machine learning models predict fermentation completion and potential issues
- **Smart Alerts**: Intelligent notifications for stuck fermentation, temperature issues, and anomalies
- **Home Assistant Integration**: Native MQTT discovery and entity management
- **Data Persistence**: Historical data storage for analysis and model training
- **Multi-sensor Support**: Flexible configuration for various sensor types
- **Production Ready**: Health checks, graceful shutdown, retry logic, and structured logging

## Installation

### Prerequisites

- Home Assistant OS or Supervised installation
- MQTT broker (Mosquitto add-on recommended)
- Fermentation monitoring hardware (compatible sensors)

### HACS Installation

1. Add this repository to HACS as a custom repository
2. Search for "Wine Fermentation Monitor" in HACS
3. Click "Install"
4. Restart Home Assistant

### Manual Installation

1. Copy the `addon` directory to `/addons/wine_fermentation_monitor/`
2. Refresh the Add-on Store
3. Install the "Wine Fermentation Monitor" add-on

## Configuration

### Basic Configuration

```yaml
mqtt:
  host: core-mosquitto
  port: 1883
  username: ""
  password: ""

sensors:
  temperature:
    enabled: true
    topic: wine/sensors/temperature

  specific_gravity:
    enabled: true
    topic: wine/sensors/sg

  ph:
    enabled: true
    topic: wine/sensors/ph

ml:
  enabled: true
  prediction_interval: 3600  # seconds

alerts:
  enabled: true
  temperature_min: 18.0
  temperature_max: 28.0
```

### Advanced Configuration

See the full configuration schema in `config.yaml` for all available options including:

- MQTT authentication and QoS settings
- Individual sensor configuration
- ML model parameters
- Alert thresholds and cooldown periods
- Logging configuration

## MQTT Topics

### Sensor Input Topics (Publish from your sensors)

- `wine/sensors/temperature` - Temperature readings (°C)
- `wine/sensors/sg` - Specific gravity readings
- `wine/sensors/ph` - pH readings
- `wine/sensors/pressure` - Pressure readings (kPa)

### Add-on Output Topics (Subscribe for predictions/alerts)

- `wine/fermentation/prediction` - ML predictions
- `wine/fermentation/status` - Current fermentation status
- `wine/fermentation/alerts` - Alert notifications

### Home Assistant Discovery

The add-on automatically publishes MQTT discovery messages to integrate with Home Assistant.

## Health Checks

The add-on exposes health check endpoints:

- `http://localhost:8099/health` - Overall health status
- `http://localhost:8099/ready` - Readiness check
- `http://localhost:8099/metrics` - Prometheus-style metrics

## Data Storage

Data is persisted in the `/data` directory:

- `/data/models/` - Trained ML models
- `/data/history/` - Historical sensor data
- `/data/logs/` - Application logs

## Machine Learning

The add-on uses scikit-learn to build predictive models:

- **Fermentation Completion Prediction**: Estimates when fermentation will complete
- **Stuck Fermentation Detection**: Identifies potential stuck fermentations early
- **Anomaly Detection**: Flags unusual readings that may indicate issues
- **Auto-retraining**: Models retrain periodically with new data

### Model Types

- Random Forest (default)
- Gradient Boosting
- Linear Regression

Configure via the `ml.model_type` option.

## Alerts

Smart alerts notify you of important events:

- **Temperature Out of Range**: Configurable min/max thresholds
- **Stuck Fermentation**: Detects when SG change is below threshold
- **pH Issues**: Alerts on extreme pH values
- **Anomaly Detection**: ML-powered anomaly alerts

Alerts are published via MQTT and can trigger Home Assistant automations.

## Logging

Structured JSON logging is enabled by default for production environments:

```json
{
  "timestamp": "2025-11-16T10:30:00Z",
  "name": "main.MQTTService",
  "level": "INFO",
  "message": "MQTT connected successfully"
}
```

Standard logging is also available for easier debugging.

## Troubleshooting

### Add-on won't start

1. Check MQTT broker is running and accessible
2. Verify MQTT credentials if authentication is enabled
3. Review add-on logs in Home Assistant
4. Check health endpoint: `http://HOMEASSISTANT_IP:8099/health`

### No sensor data

1. Verify MQTT topics match sensor configuration
2. Check sensors are publishing to correct topics
3. Enable DEBUG logging to see received messages
4. Use MQTT Explorer to verify message flow

### ML predictions not working

1. Ensure sufficient historical data (default: 100 samples)
2. Check `ml.enabled` is set to `true`
3. Verify sensors are providing consistent data
4. Review logs for model training errors

## Development

### Building Locally

```bash
docker build -t wine-monitor-addon ./addon
```

### Running Tests

```bash
cd addon/rootfs/app
python -m pytest tests/
```

## Support

- GitHub Issues: https://github.com/tipsyhomelab/wine-fermentation-monitor/issues
- Documentation: https://github.com/tipsyhomelab/wine-fermentation-monitor/wiki
- Community Forum: https://community.home-assistant.io/

## License

MIT License - see LICENSE file for details

## Credits

Developed by TipsyHomeLab for the Home Assistant community.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history.
