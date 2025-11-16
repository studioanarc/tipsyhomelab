# Wine Monitor Custom Integration

A Home Assistant custom integration for monitoring wine fermentation with dynamic sensor creation.

## Features

- 🔄 **Dynamic Sensor Creation**: Only creates sensors for available data
- 🌐 **API Integration**: Fetches data from Wine Monitor backend
- 📊 **Multiple Sensor Types**: Supports 15+ sensor types
- ⚡ **Real-time Updates**: Configurable update intervals
- 🎯 **Targeted Sensors**: Bubble rate, gravity, temperature, pH, and more
- 🔔 **Alert Support**: Built-in anomaly and threshold alerts
- 📈 **Trend Analysis**: Calculates trends for sensor data
- 🛠️ **Service Integration**: Custom Home Assistant services

## Installation

### Manual Installation

1. Copy the `wine_monitor` directory to `/config/custom_components/`:

```bash
cp -r wine_monitor /config/custom_components/
```

2. Restart Home Assistant

3. Add integration via UI:
   - Settings → Devices & Services
   - Add Integration
   - Search "Wine Monitor"

### Configuration

During setup, provide:

- **Name**: Display name for your fermentation
- **API URL**: Wine Monitor backend URL (e.g., `http://homeassistant.local:5000`)
- **Update Interval**: Seconds between updates (default: 60)
- **Webhook ID**: (Optional) For push updates

## Sensors

### Core Sensors (Always Created)

These sensors are always created if data is available:

| Entity ID | Description | Unit |
|-----------|-------------|------|
| `sensor.wine_bubble_rate` | Bubble activity | bubbles/min |
| `sensor.wine_fermentation_status` | Current status | - |
| `sensor.wine_bottling_prediction` | Days to bottling | days |
| `sensor.wine_days_fermenting` | Days since start | days |

### Optional Sensors (Created Dynamically)

Created only if your backend provides this data:

| Entity ID | Description | Unit | Source |
|-----------|-------------|------|--------|
| `sensor.wine_gravity` | Specific gravity | SG | iSpindel |
| `sensor.wine_battery` | Battery level | % | iSpindel |
| `sensor.wine_tilt` | Tilt angle | ° | iSpindel |
| `sensor.wine_temperature` | Temperature | °C | Temperature sensor |
| `sensor.wine_ph` | pH level | pH | pH sensor |
| `sensor.wine_mlf_status` | MLF status | - | pH sensor |
| `sensor.wine_pressure` | Pressure | PSI | Pressure sensor |
| `sensor.wine_abv` | Alcohol by volume | % | Calculated |
| `sensor.wine_og` | Original gravity | SG | Manual/iSpindel |
| `sensor.wine_fg` | Final gravity | SG | Manual/iSpindel |
| `sensor.wine_attenuation` | Attenuation | % | Calculated |

### Sensor Attributes

Each sensor includes additional attributes:

- `batch_id`: Unique batch identifier
- `batch_name`: Batch display name
- `start_date`: Fermentation start date
- `trend`: Percentage change from previous reading
- `last_update`: Last data update timestamp
- `source`: Data source (e.g., "iSpindel", "manual")

## Services

### wine_monitor.get_history

Retrieve historical data for a sensor.

```yaml
service: wine_monitor.get_history
data:
  sensor_type: bubble_rate
  hours: 24
```

**Parameters:**
- `sensor_type`: Sensor to get history for
- `hours`: Hours of history (default: 24)

### wine_monitor.get_alerts

Get all active alerts.

```yaml
service: wine_monitor.get_alerts
```

**Returns:**
```json
[
  {
    "type": "stuck_fermentation",
    "message": "No bubble activity for 24 hours",
    "severity": "error",
    "timestamp": "2024-11-16T10:30:00Z"
  }
]
```

### wine_monitor.refresh_data

Force immediate data refresh.

```yaml
service: wine_monitor.refresh_data
```

## API Requirements

Your Wine Monitor backend must provide these endpoints:

### GET /api/status

Returns fermentation status:

```json
{
  "batch_id": "2024-pinot-001",
  "batch_name": "Pinot Noir 2024",
  "start_date": "2024-11-01",
  "status": "Fermenting",
  "alerts": [
    {
      "type": "temperature_alert",
      "message": "Temperature outside optimal range",
      "severity": "warning"
    }
  ]
}
```

### GET /api/sensors

Returns sensor data:

```json
{
  "bubble_rate": {
    "value": 12.5,
    "trend": -2.3,
    "source": "bubble_counter"
  },
  "gravity": {
    "value": 1.015,
    "trend": -1.2,
    "source": "ispindel"
  },
  "temperature": {
    "value": 22.5,
    "source": "ds18b20"
  },
  "battery": {
    "value": 87,
    "source": "ispindel"
  }
}
```

### GET /api/history/{sensor_type}?hours=24

Returns historical data:

```json
[
  {
    "timestamp": "2024-11-16T10:00:00Z",
    "value": 12.5
  },
  {
    "timestamp": "2024-11-16T11:00:00Z",
    "value": 12.3
  }
]
```

## Configuration Example

### configuration.yaml

```yaml
# MQTT integration for real-time updates (optional)
mqtt:
  broker: localhost
  port: 1883
  username: !secret mqtt_username
  password: !secret mqtt_password
```

### Integration Setup

Configure via UI or add to `configuration.yaml`:

```yaml
wine_monitor:
  - name: "My Wine Fermentation"
    api_url: "http://localhost:5000"
    update_interval: 60
    webhook_id: "wine_monitor_webhook"
```

## Automations

### Example: Stuck Fermentation Alert

```yaml
- alias: Wine Stuck Fermentation
  trigger:
    - platform: state
      entity_id: sensor.wine_fermentation_status
      to: "Stuck Fermentation"
  action:
    - service: notify.mobile_app
      data:
        title: "🍷 Fermentation Stuck"
        message: "No activity for {{ state_attr('sensor.wine_fermentation_status', 'hours_inactive') }} hours"
```

### Example: Ready to Bottle

```yaml
- alias: Wine Ready to Bottle
  trigger:
    - platform: state
      entity_id: sensor.wine_fermentation_status
      to: "Ready to Bottle"
  action:
    - service: notify.mobile_app
      data:
        title: "🍷 Ready to Bottle!"
        message: >
          {{ state_attr('sensor.wine_fermentation_status', 'batch_name') }}
          is ready! Final ABV: {{ states('sensor.wine_abv') }}%
```

## Development

### File Structure

```
wine_monitor/
├── __init__.py              # Integration setup
├── manifest.json            # Integration metadata
├── const.py                 # Constants and configuration
├── config_flow.py           # UI configuration flow
├── sensor.py                # Sensor platform
├── services.yaml            # Service definitions
├── strings.json             # UI translations
└── README.md               # This file
```

### Adding New Sensor Types

1. Add sensor definition to `const.py`:

```python
SENSOR_TYPES = {
    "new_sensor": {
        "name": "New Sensor",
        "unit": "unit",
        "icon": "mdi:icon",
        "device_class": None,
        "state_class": "measurement",
    }
}
```

2. Ensure your API returns this sensor in `/api/sensors`

3. Restart Home Assistant

### Debug Logging

Enable debug logging in `configuration.yaml`:

```yaml
logger:
  default: info
  logs:
    custom_components.wine_monitor: debug
```

## Troubleshooting

### Integration Not Loading

1. Check logs: Settings → System → Logs
2. Verify file structure
3. Check permissions: `ls -la /config/custom_components/wine_monitor`
4. Restart Home Assistant completely

### Sensors Not Created

**This is normal!** Sensors are only created if data is available.

To verify:
1. Check API response: `curl http://your-api/api/sensors`
2. Review logs for sensor creation
3. Ensure backend is returning sensor data

### API Connection Failed

1. Test API manually: `curl http://your-api/api/status`
2. Verify URL in integration configuration
3. Check firewall/network settings
4. Review Home Assistant logs

### Data Not Updating

1. Check update interval in configuration
2. Verify backend is running
3. Test API endpoints manually
4. Check for errors in logs

## API Backend Setup

For a complete Wine Monitor backend, see:
- `/addon/` - Home Assistant Add-on
- `/examples/` - Example configurations
- Main repository documentation

## Support

- **Issues**: https://github.com/tipsyhomelab/wine-monitor/issues
- **Documentation**: https://github.com/tipsyhomelab/wine-monitor/tree/main/docs
- **Discussions**: https://github.com/tipsyhomelab/wine-monitor/discussions

## License

MIT License

## Credits

Part of the TipsyHomeLab project for monitoring wine and beer fermentation.

---

Made with 🍷 for the homebrewing community
