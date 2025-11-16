# Quick Start Guide

Get your Wine Fermentation Monitor up and running in 5 minutes!

## Prerequisites

- [ ] Home Assistant OS or Supervised installation
- [ ] MQTT broker (Mosquitto add-on) installed and running
- [ ] Fermentation monitoring sensors (e.g., iSpindel, Tilt, custom sensors)

## Step 1: Install the Add-on

### Option A: Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Click "Integrations"
3. Click the menu (⋮) → "Custom repositories"
4. Add: `https://github.com/tipsyhomelab/wine-fermentation-monitor`
5. Category: "Add-on"
6. Click "Add"
7. Search for "Wine Fermentation Monitor"
8. Click "Download"

### Option B: Manual Installation

1. Copy the `addon` folder to `/addons/wine_fermentation_monitor/`
2. Refresh the Add-on Store
3. Find "Wine Fermentation Monitor" in the list

## Step 2: Configure MQTT

Open the add-on configuration and set your MQTT settings:

```yaml
mqtt:
  host: core-mosquitto        # or your MQTT broker hostname
  port: 1883
  username: your_mqtt_user    # if authentication enabled
  password: your_mqtt_pass    # if authentication enabled
```

**Tip**: If using the Mosquitto add-on without authentication, leave username and password empty.

## Step 3: Configure Sensors

Enable the sensors you have:

```yaml
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
```

**Important**: Make sure the topics match what your sensors are publishing to!

## Step 4: Start the Add-on

1. Click "Save" to save your configuration
2. Go to the "Info" tab
3. Click "Start"
4. Click "Logs" to verify successful startup

### Expected Log Output

```
Wine Fermentation Monitor Starting
Loading configuration...
Configuration loaded successfully
MQTT connected successfully
Health check server started
All services initialized successfully
Wine Fermentation Monitor is running
```

## Step 5: Verify Health

Check the health endpoint:

```
http://YOUR_HOME_ASSISTANT_IP:8099/health
```

You should see:
```json
{
  "status": "healthy",
  "mqtt_connected": true,
  "uptime_seconds": 30
}
```

## Step 6: Set Up Your Sensors

### Example: Publishing Temperature Data

Your sensors should publish MQTT messages like:

```json
{
  "value": 22.5,
  "unit": "°C",
  "timestamp": "2025-11-16T10:30:00Z"
}
```

To the topic: `wine/sensors/temperature`

### Test with MQTT Explorer

1. Install MQTT Explorer
2. Connect to your MQTT broker
3. Publish a test message to `wine/sensors/temperature`
4. Check add-on logs to confirm receipt

## Step 7: Add Automations (Optional)

Copy examples from `examples/automations.yaml` to your Home Assistant configuration:

```yaml
automation:
  - alias: "Wine Temperature Alert"
    trigger:
      - platform: mqtt
        topic: wine/fermentation/alerts
        payload: temperature_high
    action:
      - service: notify.mobile_app
        data:
          message: "Wine temperature too high!"
```

## Troubleshooting

### Add-on Won't Start

1. **Check MQTT broker is running**
   - Supervisor → Mosquitto broker → Ensure it's started

2. **Verify configuration**
   - Check MQTT host/port are correct
   - Ensure username/password match broker settings

3. **Check logs**
   - Look for error messages
   - Common issues: MQTT connection refused, invalid config

### No Sensor Data

1. **Verify topics match**
   - Sensor publish topic = Add-on subscribe topic
   - Check for typos in topic names

2. **Check MQTT messages**
   - Use MQTT Explorer to see if messages are arriving
   - Verify message format matches expected JSON

3. **Enable debug logging**
   ```yaml
   logging:
     level: DEBUG
   ```

### Health Check Fails

1. **Wait for startup**
   - Allow 30-60 seconds for full initialization

2. **Check port not blocked**
   - Ensure port 8099 is not used by another service

3. **Verify MQTT connection**
   - Health check requires MQTT to be connected

## Next Steps

### Configure Alerts

```yaml
alerts:
  enabled: true
  temperature_min: 18.0
  temperature_max: 28.0
  sg_stuck_threshold: 0.001
  sg_stuck_hours: 48
```

### Enable Machine Learning

```yaml
ml:
  enabled: true
  prediction_interval: 3600
  min_samples_for_training: 100
```

**Note**: ML requires at least 100 sensor readings before predictions start.

### Create Dashboard

Add cards to your Lovelace dashboard:

```yaml
type: entities
title: Wine Fermentation
entities:
  - sensor.wine_temperature
  - sensor.wine_specific_gravity
  - sensor.wine_ph
  - sensor.wine_fermentation_status
```

## Common Configurations

### iSpindel Integration

```yaml
sensors:
  temperature:
    enabled: true
    topic: ispindel/YOURDEVICE/temperature
  specific_gravity:
    enabled: true
    topic: ispindel/YOURDEVICE/gravity
```

### Tilt Hydrometer Integration

```yaml
sensors:
  temperature:
    enabled: true
    topic: tilt/YOURCOLOR/temperature
  specific_gravity:
    enabled: true
    topic: tilt/YOURCOLOR/gravity
```

### Custom ESP32 Sensors

```yaml
sensors:
  temperature:
    enabled: true
    topic: wine/custom/temp
  specific_gravity:
    enabled: true
    topic: wine/custom/sg
  ph:
    enabled: true
    topic: wine/custom/ph
```

## Getting Help

- **Documentation**: See `DOCS.md` for complete reference
- **Examples**: Check `examples/` for automation ideas
- **Issues**: https://github.com/tipsyhomelab/wine-fermentation-monitor/issues
- **Community**: Home Assistant forums

## Quick Reference

| Component | Location | Purpose |
|-----------|----------|---------|
| Add-on Config | Supervisor → Wine Monitor | MQTT & sensor settings |
| Health Check | http://HA_IP:8099/health | Service status |
| Logs | Supervisor → Wine Monitor → Logs | Debugging |
| MQTT Topics | MQTT Explorer | Verify messages |

---

**That's it! Your Wine Fermentation Monitor should now be running.**

Happy brewing! 🍷
