# Troubleshooting Guide

Solutions to common issues with TipsyHomeLab installation, configuration, and operation.

---

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [MQTT Problems](#mqtt-problems)
3. [Sensor Issues](#sensor-issues)
4. [Prediction Problems](#prediction-problems)
5. [Data Issues](#data-issues)
6. [Home Assistant Integration](#home-assistant-integration)
7. [Performance Issues](#performance-issues)
8. [FAQ](#faq)

---

## Installation Issues

### Integration Not Appearing

**Symptom:** TipsyHomeLab doesn't show up in Home Assistant integrations list

**Diagnostic Steps:**
```bash
# Check if files are installed
ls -la /config/custom_components/tipsyhomelab/

# Check file permissions
ls -l /config/custom_components/tipsyhomelab/manifest.json

# Verify manifest.json is valid
cat /config/custom_components/tipsyhomelab/manifest.json
```

**Common Causes & Solutions:**

1. **Files not copied correctly**
   ```bash
   # Verify all required files exist
   ls /config/custom_components/tipsyhomelab/
   # Should see: __init__.py, manifest.json, sensor.py, etc.
   ```

2. **Incorrect permissions**
   ```bash
   sudo chown -R homeassistant:homeassistant /config/custom_components/tipsyhomelab
   sudo chmod -R 755 /config/custom_components/tipsyhomelab
   ```

3. **Browser cache**
   - Hard refresh: Ctrl + Shift + R (Windows/Linux)
   - Or: Cmd + Shift + R (Mac)
   - Or clear browser cache completely

4. **Home Assistant not restarted**
   ```bash
   # Restart Home Assistant
   ha core restart
   # Or from UI: Configuration → Server Controls → Restart
   ```

**Verification:**
```bash
# Check Home Assistant logs
ha core logs | grep tipsyhomelab

# Should see:
# "Loading custom integration tipsyhomelab"
```

### Import Errors

**Symptom:** Errors in logs about missing Python modules

```
ERROR (MainThread) [homeassistant.setup] Error during setup of component tipsyhomelab
ModuleNotFoundError: No module named 'paho.mqtt'
```

**Solutions:**

1. **Install missing dependencies**
   ```bash
   # Enter Home Assistant container
   docker exec -it homeassistant /bin/bash

   # Install requirements
   pip install -r /config/custom_components/tipsyhomelab/requirements.txt

   # Exit and restart
   exit
   ha core restart
   ```

2. **Check manifest.json requirements**
   ```json
   {
     "requirements": [
       "paho-mqtt==1.6.1",
       "scikit-learn==1.3.0",
       "pandas==2.0.0"
     ]
   }
   ```

3. **Manual installation**
   ```bash
   pip install paho-mqtt==1.6.1
   pip install scikit-learn==1.3.0
   pip install pandas==2.0.0
   ```

### Configuration Invalid

**Symptom:** "Invalid config for [tipsyhomelab]"

**Common YAML Errors:**

1. **Indentation (spaces, not tabs)**
   ```yaml
   # WRONG (using tabs)
   tipsyhomelab:
   ␉batches:  # This is a tab - WRONG!

   # CORRECT (using spaces)
   tipsyhomelab:
     batches:  # Two spaces
       - name: "Batch 1"  # Four spaces
   ```

2. **Missing quotes for special characters**
   ```yaml
   # WRONG
   name: Batch #1

   # CORRECT
   name: "Batch #1"
   ```

3. **Incorrect data types**
   ```yaml
   # WRONG
   port: "1883"  # String instead of integer

   # CORRECT
   port: 1883  # Integer
   ```

**Validation:**
```bash
# Check configuration
ha core check

# View full config
ha core config | grep -A 50 tipsyhomelab
```

---

## MQTT Problems

### Cannot Connect to Broker

**Symptom:** "Failed to connect to MQTT broker"

**Diagnostic Steps:**

1. **Check broker is running**
   ```bash
   # If using Mosquitto add-on
   ha addons info core_mosquitto

   # If external broker
   sudo systemctl status mosquitto
   ```

2. **Test connection manually**
   ```bash
   # Try to connect
   mosquitto_sub -h localhost -p 1883 -u username -P password -t test/topic

   # If TLS
   mosquitto_sub -h localhost -p 8883 -u username -P password \
     --cafile /config/certs/ca.crt -t test/topic
   ```

3. **Check firewall**
   ```bash
   # Check if port is open
   sudo netstat -tulpn | grep 1883

   # Test from remote
   telnet mqtt-broker-ip 1883
   ```

**Common Causes & Solutions:**

1. **Wrong broker address**
   - Use `localhost` if broker is on same machine
   - Use IP address for external broker
   - Avoid using `127.0.0.1` in Docker (use `host.docker.internal`)

2. **Incorrect credentials**
   ```yaml
   # Check secrets.yaml
   mqtt_username: correctusername
   mqtt_password: correctpassword
   ```

3. **Broker not accepting connections**
   ```bash
   # Check Mosquitto config
   cat /etc/mosquitto/mosquitto.conf

   # Should have:
   listener 1883
   allow_anonymous false
   password_file /etc/mosquitto/passwd
   ```

4. **Port blocked**
   ```bash
   # Open port in firewall
   sudo ufw allow 1883/tcp
   ```

### Messages Not Being Received

**Symptom:** Sensors publishing but TipsyHomeLab not receiving data

**Diagnostic Steps:**

1. **Verify messages are published**
   ```bash
   # Subscribe to all topics
   mosquitto_sub -h localhost -u username -P password -t '#' -v

   # Subscribe to specific batch
   mosquitto_sub -h localhost -u username -P password -t 'tipsylab/batch1/#' -v
   ```

2. **Check topic names**
   ```bash
   # Compare configured topic vs actual topic
   # Configuration:
   bubble_counter: "tipsylab/batch1/bubbles"

   # Published topic (from mosquitto_sub):
   tipsylab/batch1/bubble  # WRONG - missing 's'
   ```

3. **Verify message format**
   ```bash
   # Check if message is valid JSON
   echo '{"count":1,"timestamp":1699999999000}' | jq .

   # If error, fix JSON formatting
   ```

**Common Causes & Solutions:**

1. **Topic mismatch**
   - Check for typos
   - Check case sensitivity
   - Check for extra spaces

2. **QoS mismatch**
   ```yaml
   # Try QoS 1 for reliability
   mqtt:
     qos: 1
   ```

3. **Message not retained**
   ```python
   # Publish with retained flag
   client.publish(topic, payload, retain=True)
   ```

4. **Subscription not active**
   ```bash
   # Check Home Assistant logs
   ha core logs | grep "Subscribed to"
   ```

### High MQTT Latency

**Symptom:** Delayed sensor updates

**Diagnostic:**
```bash
# Monitor message timestamps
mosquitto_sub -h localhost -u user -P pass -t 'tipsylab/#' -v

# Check broker load
mosquitto_sub -h localhost -u user -P pass -t '$SYS/#' -v
```

**Solutions:**

1. **Reduce update frequency**
   ```cpp
   // In sensor code
   delay(60000);  // Update every minute instead of every second
   ```

2. **Check network**
   ```bash
   # Ping broker
   ping mqtt-broker-ip

   # Check WiFi signal (for sensors)
   # Monitor RSSI in messages
   ```

3. **Broker resources**
   ```bash
   # Check CPU/memory
   top
   htop

   # Increase broker limits
   # Edit /etc/mosquitto/mosquitto.conf
   max_connections 1000
   max_queued_messages 10000
   ```

---

## Sensor Issues

### Bubble Counter Not Detecting Bubbles

**Symptom:** Zero bubble count or not incrementing

**Diagnostic Steps:**

1. **Check sensor physically**
   - LED working? (use phone camera to see IR)
   - Photodiode properly positioned?
   - Bubble passing through detection zone?

2. **Test sensor output**
   ```cpp
   // Add debug output to code
   Serial.print("Sensor reading: ");
   Serial.println(analogRead(SENSOR_PIN));
   ```

3. **Verify MQTT publishing**
   ```bash
   # Monitor MQTT topic
   mosquitto_sub -h localhost -u user -P pass -t 'tipsylab/batch1/bubbles' -v
   ```

**Common Causes & Solutions:**

1. **Threshold too high/low**
   ```cpp
   // Adjust threshold value
   const int THRESHOLD = 512;  // Try 400-700

   // Or auto-calibrate
   int baseline = analogRead(SENSOR_PIN);
   int threshold = baseline - 100;
   ```

2. **Debounce time too long**
   ```cpp
   // Reduce debounce
   const int DEBOUNCE_MS = 50;  // Instead of 500
   ```

3. **Sensor misaligned**
   - Ensure LED and photodiode face each other
   - Check bubble path passes between them
   - Try different position on airlock

4. **Ambient light interference**
   ```cpp
   // Shield sensor from light
   // Use black heat shrink tubing
   // Or add IR filter
   ```

5. **Power supply**
   ```cpp
   // Check voltage
   Serial.println(analogRead(A0) * 3.3 / 1023.0);  // Should be ~3.3V
   ```

### iSpindel Not Reporting

**Symptom:** No data from iSpindel

**Diagnostic Steps:**

1. **Check iSpindel status**
   - LED blinking? (indicates WiFi connection)
   - Battery charged? (>3.7V)
   - In deep sleep? (wakes every 15 min by default)

2. **Check WiFi connection**
   ```bash
   # Check DHCP leases
   cat /var/lib/dhcp/dhcpd.leases | grep iSpindel

   # Ping iSpindel (only when awake)
   ping ispindel-ip-address
   ```

3. **Check configuration**
   - Access iSpindel portal (when awake)
   - Verify MQTT settings
   - Check topic name
   - Verify interval setting

**Common Causes & Solutions:**

1. **Wrong WiFi credentials**
   - Reset iSpindel
   - Connect to iSpindel AP
   - Reconfigure WiFi

2. **Wrong MQTT settings**
   ```
   Service: MQTT
   Server: 192.168.1.100  # Correct IP
   Port: 1883
   Username: tipsylab
   Password: ********
   Topic: tipsylab/batch1/ispindel  # Match config!
   ```

3. **Battery dead**
   - Charge battery
   - Replace if old (>1 year)
   - Check battery voltage in web interface

4. **Too long interval**
   ```
   # Change sleep interval
   Interval: 900  # 15 minutes (default)
   # During active fermentation, use shorter:
   Interval: 300  # 5 minutes
   ```

5. **Out of range**
   - Move closer to WiFi router
   - Add WiFi extender
   - Check RSSI value (should be > -80 dBm)

### Temperature Readings Incorrect

**Symptom:** Temperature sensor showing wrong values

**Diagnostic Steps:**

1. **Test sensor**
   ```cpp
   // Read and print temperature
   sensors.requestTemperatures();
   float temp = sensors.getTempCByIndex(0);
   Serial.println(temp);
   ```

2. **Compare to reference**
   - Use calibrated thermometer
   - Ice water test (should read 0°C)
   - Room temperature test

**Common Causes & Solutions:**

1. **Sensor reading -127°C or 85°C**
   - Indicates connection problem
   - Check wiring
   - Add/check pull-up resistor (4.7kΩ)
   ```cpp
   // Verify pull-up on data line
   pinMode(ONE_WIRE_BUS, INPUT_PULLUP);
   ```

2. **Offset calibration needed**
   ```cpp
   // Add offset
   float tempRaw = sensors.getTempCByIndex(0);
   float tempCorrected = tempRaw - 0.5;  // If reads 0.5°C high
   ```

3. **Sensor in wrong location**
   - Not in wort (reading ambient instead)
   - Not using thermowell
   - Thermal lag from poor contact

4. **Multiple sensors conflict**
   ```cpp
   // Specify sensor by address
   DeviceAddress sensor1 = {0x28, 0xFF, 0x64, 0x1E, 0x8C, 0x3C, 0x03, 0xB4};
   sensors.requestTemperaturesByAddress(sensor1);
   ```

---

## Prediction Problems

### No Predictions Available

**Symptom:** "Insufficient data for predictions"

**Requirements Check:**
```yaml
# Minimum requirements:
- 48 hours of continuous data
- At least one of: bubble rate OR gravity
- No large data gaps (> 6 hours)
```

**Diagnostic:**
```bash
# Check entity states
ha state get sensor.tipsylab_batch1_predicted_completion

# Check logs
ha core logs | grep prediction
```

**Solutions:**

1. **Wait for more data**
   - Need at least 48 hours
   - 72+ hours for accurate predictions

2. **Check data continuity**
   ```bash
   # Verify recent data
   mosquitto_sub -h localhost -u user -P pass -t 'tipsylab/batch1/#' -v

   # Should see regular updates
   ```

3. **Verify sensors working**
   - Check bubble counter reporting
   - Check gravity sensor reporting
   - Check for sensor errors

### Predictions Seem Wrong

**Symptom:** Predicted values don't match reality

**Diagnostic:**

1. **Check model confidence**
   ```yaml
   # Low confidence = unreliable
   sensor.tipsylab_batch1_prediction_confidence
   # Should be > 0.70 for good predictions
   ```

2. **Verify input data quality**
   - Gravity readings accurate?
   - Temperature stable?
   - Bubble counter working correctly?

3. **Check fermentation assumptions**
   - Unusual yeast strain?
   - Non-standard conditions?
   - Contamination?

**Common Causes & Solutions:**

1. **Not enough data yet**
   - Predictions improve over time
   - Early predictions (< 72h) are rough estimates

2. **Unusual fermentation**
   ```yaml
   # Override predictions if needed
   predictions:
     overrides:
       final_gravity: 1.002  # Manual override
   ```

3. **Temperature fluctuations**
   - Stabilize temperature
   - Wait for pattern to establish

4. **Stuck fermentation**
   - Model assumes normal fermentation
   - If stuck, predictions will be wrong
   - Check fermentation status

5. **Wrong initial values**
   ```yaml
   # Verify starting gravity was correct
   original_gravity: 1.055  # Check this!
   ```

### Predictions Keep Changing

**Symptom:** Completion date jumps around

**Expected Behavior:**
- Normal during phase transitions (lag → active → slowing)
- Should stabilize after 96+ hours

**Causes:**

1. **Active phase transitions**
   - Wait 24 hours for stabilization
   - Normal during peak → slowing transition

2. **Temperature changes**
   - Affects fermentation rate
   - Stabilize environment

3. **Fermentation irregularities**
   - Stuck then restarted
   - Nutrient added
   - Yeast behavior changed

**Solutions:**

1. **Wait for stabilization**
   - Don't act on single prediction
   - Watch trend over 24-48 hours

2. **Check confidence intervals**
   ```yaml
   # Wide intervals = uncertain
   predicted_date: 2024-11-20
   confidence_interval:
     lower: 2024-11-18  # ± 2 days = uncertain
     upper: 2024-11-22
   ```

3. **Verify data quality**
   - Check for sensor glitches
   - Verify readings make sense

---

## Data Issues

### Missing Historical Data

**Symptom:** History graph shows gaps

**Diagnostic:**
```bash
# Check recorder database
sqlite3 /config/home-assistant_v2.db "SELECT * FROM states WHERE entity_id='sensor.tipsylab_batch1_gravity' LIMIT 10;"
```

**Common Causes & Solutions:**

1. **Recorder not configured**
   ```yaml
   # Add to configuration.yaml
   recorder:
     include:
       domains:
         - sensor
       entity_globs:
         - sensor.tipsylab_*
   ```

2. **Database purge**
   ```yaml
   # Increase retention
   recorder:
     purge_keep_days: 90  # Instead of default 10
   ```

3. **Sensor unavailable**
   - Check sensor connection
   - Verify MQTT messages

### InfluxDB Not Storing Data

**Symptom:** Data not showing in Grafana

**Diagnostic:**
```bash
# Check InfluxDB
influx -database tipsyhomelab
> SELECT * FROM fermentation LIMIT 10;

# Check InfluxDB logs
docker logs influxdb
```

**Solutions:**

1. **Verify InfluxDB integration**
   ```yaml
   influxdb:
     host: localhost
     port: 8086
     database: tipsyhomelab
     username: !secret influxdb_user
     password: !secret influxdb_pass
     include:
       entity_globs:
         - sensor.tipsylab_*
   ```

2. **Check database exists**
   ```bash
   influx
   > SHOW DATABASES;
   > CREATE DATABASE tipsyhomelab;
   ```

3. **Check credentials**
   ```bash
   influx -username user -password pass
   ```

---

## Home Assistant Integration

### Entities Not Showing

**Symptom:** TipsyHomeLab entities missing from Home Assistant

**Diagnostic:**
```bash
# List all entities
ha state list | grep tipsylab

# Check specific entity
ha state get sensor.tipsylab_batch1_bubble_rate
```

**Solutions:**

1. **Check MQTT discovery**
   ```bash
   # Monitor discovery messages
   mosquitto_sub -h localhost -u user -P pass -t 'homeassistant/#' -v
   ```

2. **Manually add entities**
   ```yaml
   # See API.md for manual sensor configuration
   mqtt:
     sensor:
       - name: "Batch 1 Bubble Rate"
         state_topic: "tipsylab/batch1/bubbles"
         # ...
   ```

3. **Restart Home Assistant**
   ```bash
   ha core restart
   ```

### Dashboard Cards Not Working

**Symptom:** Lovelace cards showing errors

**Common Errors:**

1. **Entity not found**
   ```yaml
   # Check entity ID spelling
   entities:
     - sensor.tipsylab_batch1_bubble_rate  # Correct spelling?
   ```

2. **Invalid card configuration**
   ```yaml
   # Validate YAML
   type: entities
   entities:
     - sensor.tipsylab_batch1_gravity  # List format
   ```

3. **Custom card not installed**
   - Install required custom card via HACS
   - Clear browser cache

---

## Performance Issues

### High CPU Usage

**Symptom:** Home Assistant slow, high CPU

**Diagnostic:**
```bash
# Check CPU usage
top
htop

# Check Home Assistant processes
docker stats homeassistant
```

**Solutions:**

1. **Reduce update frequency**
   ```yaml
   # Increase sensor intervals
   performance:
     sensor_update_interval: 300  # 5 minutes instead of 60 seconds
   ```

2. **Disable predictions temporarily**
   ```yaml
   predictions:
     enabled: false
   ```

3. **Limit data retention**
   ```yaml
   recorder:
     purge_keep_days: 30  # Instead of 90
   ```

4. **Use lighter model**
   ```yaml
   predictions:
     model: polynomial  # Instead of gradient_boosting
   ```

### Slow Predictions

**Symptom:** Prediction updates take long time

**Solutions:**

1. **Reduce update frequency**
   ```yaml
   predictions:
     update_interval: 7200  # Every 2 hours instead of 1 hour
   ```

2. **Use simpler model**
   ```yaml
   predictions:
     model: polynomial
     parameters:
       degree: 2  # Instead of 3
   ```

3. **Reduce data points**
   ```yaml
   performance:
     max_data_points: 10000  # Limit historical data used
   ```

---

## FAQ

### Q: Can I monitor multiple batches simultaneously?

**A:** Yes! Configure multiple batches in `configuration.yaml`:
```yaml
batches:
  - name: "Batch 1"
    sensors:
      bubble_counter: "tipsylab/batch1/bubbles"

  - name: "Batch 2"
    sensors:
      bubble_counter: "tipsylab/batch2/bubbles"
```

### Q: Do I need all sensors?

**A:** No. Minimum requirement is:
- Bubble counter OR hydrometer (iSpindel/Tilt)
- Temperature sensor strongly recommended

### Q: Can I use without Home Assistant?

**A:** TipsyHomeLab is designed for Home Assistant, but the MQTT API is open - you could build your own frontend. See [API.md](API.md).

### Q: How accurate are predictions?

**A:** Depends on:
- Data quality: ±0.001-0.003 SG
- Time: ±0.5-3 days (improves with time)
- Conditions: Better with stable temperature

### Q: Can I train models on my own data?

**A:** Yes! Models automatically train on your completed batches. Manual training coming in future release.

### Q: Does it work with beer/cider/mead?

**A:** Yes! Configure batch type:
```yaml
type: beer  # or cider, mead, kombucha
```

### Q: Is internet required?

**A:** No, everything runs locally. Internet only needed for:
- Initial installation (downloads)
- External integrations (optional)
- Remote access (optional)

### Q: Can I export data?

**A:** Yes:
```yaml
data_storage:
  csv_export:
    enabled: true
    path: /config/exports/
```

### Q: What if fermentation gets stuck?

**A:** TipsyHomeLab can detect stuck fermentation:
```yaml
alerts:
  conditions:
    - type: stuck_fermentation
      enabled: true
```

### Q: Can I use imperial units?

**A:** Yes:
```yaml
unit_system: imperial  # or metric
```

---

## Getting Help

If your issue isn't covered here:

1. **Check logs**: `ha core logs | grep tipsyhomelab`
2. **Search GitHub Issues**: [github.com/yourusername/tipsyhomelab/issues](https://github.com/yourusername/tipsyhomelab/issues)
3. **Ask in Discussions**: [github.com/yourusername/tipsyhomelab/discussions](https://github.com/yourusername/tipsyhomelab/discussions)
4. **Join Discord**: [discord.gg/tipsyhomelab](https://discord.gg/tipsyhomelab)

**When reporting issues, include:**
- Home Assistant version
- TipsyHomeLab version
- Relevant logs
- Configuration (sanitized)
- Steps to reproduce
- Expected vs actual behavior
