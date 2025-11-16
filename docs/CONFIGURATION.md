# Configuration Guide

Complete reference for all TipsyHomeLab configuration options.

---

## Table of Contents

1. [Configuration Methods](#configuration-methods)
2. [Basic Configuration](#basic-configuration)
3. [Batch Configuration](#batch-configuration)
4. [Sensor Configuration](#sensor-configuration)
5. [Prediction Settings](#prediction-settings)
6. [Alert Configuration](#alert-configuration)
7. [Advanced Options](#advanced-options)
8. [Configuration Examples](#configuration-examples)

---

## Configuration Methods

TipsyHomeLab supports two configuration methods:

### Method 1: UI Configuration (Recommended)

1. Go to **Configuration → Integrations**
2. Click **Add Integration**
3. Search for "TipsyHomeLab"
4. Follow the configuration wizard

**Pros**:
- User-friendly interface
- Validation of inputs
- Easy to modify
- No YAML knowledge required

**Cons**:
- Limited to common options
- Cannot set all advanced features

### Method 2: YAML Configuration

Add to `configuration.yaml`:

```yaml
tipsyhomelab:
  # Configuration here
```

**Pros**:
- Full control over all options
- Can use templates and secrets
- Version control friendly
- Supports advanced features

**Cons**:
- Requires YAML knowledge
- Syntax errors can break config
- Must restart HA after changes

**Best Practice**: Use UI for basic setup, add YAML for advanced features.

---

## Basic Configuration

### Minimum Configuration

```yaml
tipsyhomelab:
  mqtt:
    broker: localhost

  batches:
    - name: "My Batch"
      sensors:
        bubble_counter: "tipsylab/batch1/bubbles"
```

### Complete Basic Configuration

```yaml
tipsyhomelab:
  # MQTT Connection
  mqtt:
    broker: localhost
    port: 1883
    username: !secret mqtt_username
    password: !secret mqtt_password
    discovery_prefix: homeassistant
    client_id: tipsyhomelab

  # Global Settings
  unit_system: metric  # or imperial
  timezone: America/New_York

  # Batches
  batches:
    - name: "Batch 1"
      type: petnat
      sensors:
        bubble_counter: "tipsylab/batch1/bubbles"
        temperature: "tipsylab/batch1/temp"
```

---

## Batch Configuration

Each batch represents a fermentation vessel being monitored.

### Batch Parameters

```yaml
batches:
  - name: "Spring Blossom Pet Nat"

    # Batch Type
    type: petnat  # Options: petnat, beer, wine, cider, kombucha, mead, custom

    # Batch Metadata
    started: "2024-11-01"  # ISO date format
    recipe_id: "recipe_123"  # Optional recipe reference
    volume: 20  # Liters

    # Target Values
    target_gravity: 1.002
    target_pressure: 3.5  # bar
    target_co2: 6.0  # g/L

    # Bottle Information (for Pet Nat)
    bottle_volume: 750  # mL
    bottle_type: champagne  # Options: champagne, beer, custom
    headspace: 25  # mL

    # Safety Limits
    max_pressure: 6.0  # bar
    max_temperature: 30  # Celsius
    min_temperature: 10  # Celsius

    # Sensors (see Sensor Configuration section)
    sensors:
      bubble_counter: "tipsylab/batch1/bubbles"
      temperature: "tipsylab/batch1/temp"

    # Predictions (see Prediction Settings section)
    predictions:
      enabled: true

    # Alerts (see Alert Configuration section)
    alerts:
      enabled: true
```

### Batch Types

Each batch type has specific defaults and behavior:

#### Pet Nat
```yaml
type: petnat
# Defaults:
# - target_pressure: 3.5 bar
# - target_co2: 6.0 g/L
# - max_pressure: 6.0 bar
# - bottle_type: champagne
# - Enables pressure calculations
# - Provides bottling window predictions
```

#### Beer
```yaml
type: beer
# Defaults:
# - target_gravity: 1.010
# - target_co2: 5.0 g/L (depends on style)
# - Enables ABV calculations
# - Provides carbonation predictions
```

#### Wine (Still)
```yaml
type: wine
# Defaults:
# - target_gravity: 0.995
# - Dry fermentation typical
# - Extended fermentation timeline
# - No carbonation calculations
```

#### Cider
```yaml
type: cider
# Defaults:
# - target_gravity: 1.000
# - target_co2: 4.0 g/L
# - Similar to beer but different sugars
```

#### Mead
```yaml
type: mead
# Defaults:
# - target_gravity: 1.000-1.010
# - Very long fermentation
# - Different prediction models
```

#### Custom
```yaml
type: custom
# No defaults - must specify all parameters
# Use for experimental fermentations
```

---

## Sensor Configuration

Configure which sensors to use for each batch.

### Bubble Counter

```yaml
sensors:
  bubble_counter:
    topic: "tipsylab/batch1/bubbles"

    # Optional settings
    rate_window: 300  # Calculate rate over 5 minutes
    smoothing: true   # Apply moving average
    smoothing_window: 10  # Number of readings to average

    # Debouncing
    min_interval: 100  # Minimum ms between bubbles

    # Calibration
    multiplier: 1.0  # Adjust if counter is off
```

### iSpindel

```yaml
sensors:
  ispindel:
    topic: "tipsylab/batch1/ispindel"

    # Calibration polynomial (from calibration spreadsheet)
    calibration:
      - 0.00001217   # x³ coefficient
      - -0.0064      # x² coefficient
      - 0.0912       # x coefficient
      - 0.9994       # constant

    # Temperature compensation
    temp_compensation: true
    reference_temp: 20  # Celsius

    # Battery monitoring
    battery_alert: 3.7  # Alert when voltage drops below

    # Update interval
    expected_interval: 900  # seconds (15 minutes)
    stale_timeout: 1800  # Mark stale if no update for 30 min
```

### Tilt Hydrometer

```yaml
sensors:
  tilt:
    topic: "tipsylab/batch1/tilt"
    color: orange  # Tilt color

    # Unit conversion
    temp_units: F  # Source units (F or C)
    convert_to: C  # Convert to Celsius

    # Calibration offsets
    gravity_offset: 0.002  # Add/subtract from reading
    temp_offset: -1.0  # Adjust temperature
```

### Temperature Sensor

```yaml
sensors:
  temperature:
    topic: "tipsylab/batch1/temp"

    # Sensor type
    sensor_type: ds18b20  # Options: ds18b20, dht22, bme280

    # Calibration
    offset: 0.0  # Temperature offset in degrees

    # Filtering
    smoothing: true
    smoothing_window: 5

    # Placement
    placement: wort  # Options: wort, ambient, chamber
```

### pH Sensor

```yaml
sensors:
  ph:
    topic: "tipsylab/batch1/ph"

    # Calibration
    calibrated: true
    last_calibration: "2024-11-01"

    # Temperature compensation
    temp_compensation: true
    compensation_slope: 0.003  # pH units per degree C

    # Alerts
    min_ph: 3.0
    max_ph: 4.5
```

### Pressure Sensor

```yaml
sensors:
  pressure:
    topic: "tipsylab/batch1/pressure"

    # Sensor specifications
    sensor_type: transducer  # Options: transducer, gauge
    max_range: 10.0  # bar

    # Calibration
    offset: 0.0  # Atmospheric pressure offset
    multiplier: 1.0

    # Safety
    alert_threshold: 5.5  # bar
    critical_threshold: 6.0  # bar
```

### Multiple Sensors of Same Type

```yaml
sensors:
  temperature:
    - name: wort_temp
      topic: "tipsylab/batch1/temp/wort"
      placement: wort

    - name: ambient_temp
      topic: "tipsylab/batch1/temp/ambient"
      placement: ambient

  # Use specific sensor for calculations
  primary_temperature: wort_temp
```

---

## Prediction Settings

Configure machine learning predictions for fermentation completion.

### Basic Predictions

```yaml
predictions:
  enabled: true

  # Model selection
  model: auto  # Options: auto, linear, polynomial, ml

  # Data requirements
  min_data_points: 48  # Minimum hours of data
  update_interval: 3600  # Recalculate every hour
```

### Advanced Predictions

```yaml
predictions:
  enabled: true
  model: ml

  # Model parameters
  parameters:
    algorithm: gradient_boosting  # Options: linear, polynomial, gradient_boosting, lstm

    # Polynomial degree (for polynomial model)
    degree: 3

    # ML hyperparameters
    learning_rate: 0.1
    n_estimators: 100
    max_depth: 5

  # Features to use
  features:
    - bubble_rate
    - gravity
    - temperature
    - time_elapsed
    - rate_of_change

  # Prediction targets
  targets:
    completion_date: true
    final_gravity: true
    bottle_pressure: true  # For Pet Nat
    residual_sugar: true

  # Confidence intervals
  confidence_level: 0.95  # 95% confidence

  # Model training
  retrain_interval: 86400  # Retrain daily
  training_window: 604800  # Use last 7 days of data

  # Validation
  cross_validation: true
  validation_split: 0.2

  # Persistence
  save_model: true
  model_path: /config/tipsyhomelab/models/
```

### Prediction Overrides

```yaml
predictions:
  enabled: true

  # Override auto-predictions
  overrides:
    final_gravity: 1.002  # Force specific final gravity
    completion_date: "2024-11-20"  # Force specific date

  # Adjust predictions
  adjustments:
    completion_days_offset: 2  # Add 2 days to prediction
    gravity_offset: 0.001  # Adjust gravity prediction
```

---

## Alert Configuration

Configure notifications for various fermentation events.

### Basic Alerts

```yaml
alerts:
  enabled: true

  # Alert channels
  channels:
    - notify.mobile_app
    - notify.email

  # Alert conditions
  conditions:
    - type: fermentation_started
      enabled: true

    - type: fermentation_slowing
      enabled: true
      threshold: 10  # bubbles/min

    - type: fermentation_complete
      enabled: true
      threshold: 2  # bubbles/min for 24 hours

    - type: bottling_window
      enabled: true
      advance_notice: 24  # hours
```

### Advanced Alerts

```yaml
alerts:
  enabled: true

  channels:
    - service: notify.mobile_app
      priority: high

    - service: notify.email
      priority: normal
      recipient: brewer@example.com

    - service: notify.pushover
      priority: emergency
      user_key: !secret pushover_user
      api_token: !secret pushover_token

  conditions:
    # Temperature alerts
    - type: temperature_high
      enabled: true
      threshold: 25  # Celsius
      duration: 1800  # Alert if high for 30 minutes
      repeat: 3600  # Repeat alert every hour
      channels:
        - notify.mobile_app
        - notify.pushover

    - type: temperature_low
      enabled: true
      threshold: 15
      duration: 1800

    # Pressure alerts (Pet Nat)
    - type: pressure_high
      enabled: true
      threshold: 5.5  # bar
      critical_threshold: 6.0  # bar (immediate alert)
      channels:
        - notify.mobile_app
        - notify.pushover
      message: "DANGER: Bottle pressure at {pressure} bar!"

    # Activity alerts
    - type: stuck_fermentation
      enabled: true
      detection:
        max_bubble_rate: 5  # Less than 5 bubbles/min
        duration: 21600  # For 6 hours
        min_gravity: 1.020  # But gravity still high

    - type: rapid_fermentation
      enabled: true
      threshold: 100  # bubbles/min
      message: "Fermentation very active - check for overflow"

    # Completion alerts
    - type: bottling_window_open
      enabled: true
      advance_notice: 48  # hours
      message: "Bottling window opens in 2 days (estimated)"

    - type: bottling_window_closing
      enabled: true
      advance_notice: 12  # hours
      message: "Last chance to bottle! Window closes in 12 hours"

    # Sensor alerts
    - type: sensor_offline
      enabled: true
      timeout: 3600  # Alert if no data for 1 hour
      sensors:
        - ispindel
        - temperature

    - type: battery_low
      enabled: true
      threshold: 3.7  # volts
      sensors:
        - ispindel
        - tilt

  # Quiet hours
  quiet_hours:
    enabled: true
    start: "22:00"
    end: "08:00"
    exceptions:
      - pressure_high
      - temperature_critical

  # Rate limiting
  rate_limit:
    max_alerts_per_hour: 5
    cooldown_period: 300  # 5 minutes between same alert type
```

### Custom Alert Conditions

```yaml
alerts:
  custom_conditions:
    - name: perfect_bottling_time
      condition: |
        {{ states('sensor.tipsylab_batch1_gravity')|float < 1.004 and
           states('sensor.tipsylab_batch1_gravity')|float > 1.002 and
           states('sensor.tipsylab_batch1_bubble_rate')|float < 15 }}
      message: "Perfect time to bottle Pet Nat!"
      channels:
        - notify.mobile_app
```

---

## Advanced Options

### Data Storage

```yaml
data_storage:
  # InfluxDB integration
  influxdb:
    enabled: true
    host: localhost
    port: 8086
    database: tipsyhomelab
    username: !secret influxdb_user
    password: !secret influxdb_pass
    measurement: fermentation

    # Retention policy
    retention_days: 365

    # What to store
    fields:
      - bubble_rate
      - gravity
      - temperature
      - pressure
      - predictions

  # CSV Export
  csv_export:
    enabled: true
    path: /config/tipsyhomelab/exports/
    interval: 86400  # Export daily
    include_predictions: true
```

### Logging

```yaml
logging:
  level: info  # Options: debug, info, warning, error

  # Component-specific logging
  components:
    sensors: debug
    predictions: info
    mqtt: warning

  # Log file
  log_file: /config/tipsyhomelab/tipsyhomelab.log
  max_size: 10485760  # 10 MB
  backup_count: 5
```

### Performance

```yaml
performance:
  # Update intervals
  sensor_update_interval: 60  # seconds
  prediction_update_interval: 3600  # seconds

  # Data retention
  history_days: 90  # Keep 90 days in Home Assistant

  # Processing
  batch_processing: true
  async_operations: true

  # Memory limits
  max_data_points: 100000
  data_compression: true
```

### Integration

```yaml
integrations:
  # Grafana
  grafana:
    enabled: true
    url: http://localhost:3000
    api_key: !secret grafana_api_key
    dashboard_id: tipsyhomelab

  # Brewersfriend
  brewersfriend:
    enabled: true
    api_key: !secret brewersfriend_api_key
    auto_import_recipes: true

  # Brewfather
  brewfather:
    enabled: true
    user_key: !secret brewfather_user_key
    api_key: !secret brewfather_api_key

  # Node-RED
  nodered:
    enabled: true
    webhook_url: http://localhost:1880/tipsyhomelab
```

### Advanced MQTT

```yaml
mqtt:
  broker: localhost
  port: 1883
  username: !secret mqtt_username
  password: !secret mqtt_password

  # TLS/SSL
  tls:
    enabled: true
    ca_cert: /config/certs/ca.crt
    client_cert: /config/certs/client.crt
    client_key: /config/certs/client.key
    insecure: false

  # QoS and retention
  qos: 1  # 0, 1, or 2
  retain: true

  # Will/testament
  will:
    topic: tipsylab/status
    payload: offline
    qos: 1
    retain: true

  # Discovery
  discovery: true
  discovery_prefix: homeassistant

  # Birth message
  birth:
    topic: tipsylab/status
    payload: online
```

---

## Configuration Examples

### Example 1: Minimal Pet Nat Setup

```yaml
tipsyhomelab:
  mqtt:
    broker: localhost
    username: !secret mqtt_user
    password: !secret mqtt_pass

  batches:
    - name: "Pet Nat Experiment"
      type: petnat
      sensors:
        bubble_counter: "tipsylab/petnat/bubbles"
        temperature: "tipsylab/petnat/temp"
```

### Example 2: Full iSpindel Setup

```yaml
tipsyhomelab:
  mqtt:
    broker: 192.168.1.100
    port: 1883
    username: !secret mqtt_user
    password: !secret mqtt_pass

  batches:
    - name: "Belgian Pale Ale"
      type: beer
      started: "2024-11-01"
      volume: 20

      target_gravity: 1.010

      sensors:
        ispindel:
          topic: "ispindel/batch1"
          calibration:
            - 0.00001217
            - -0.0064
            - 0.0912
            - 0.9994
          battery_alert: 3.7

        temperature:
          topic: "ispindel/batch1"  # Same topic, extracts temp

      predictions:
        enabled: true
        model: polynomial
        parameters:
          degree: 3

      alerts:
        enabled: true
        channels:
          - notify.mobile_app
        conditions:
          - type: fermentation_complete
            threshold: 2
          - type: stuck_fermentation
```

### Example 3: Multi-Batch Brewery

```yaml
tipsyhomelab:
  mqtt:
    broker: localhost

  batches:
    # Fermenter 1 - Pet Nat
    - name: "Pet Nat Spring 2024"
      type: petnat
      sensors:
        bubble_counter: "tipsylab/ferm1/bubbles"
        ispindel: "ispindel/ferm1"
        temperature: "tipsylab/ferm1/temp"
        pressure: "tipsylab/ferm1/pressure"
      predictions:
        enabled: true
      alerts:
        enabled: true
        channels: [notify.brewmaster]

    # Fermenter 2 - IPA
    - name: "West Coast IPA"
      type: beer
      sensors:
        bubble_counter: "tipsylab/ferm2/bubbles"
        tilt:
          topic: "tilt/orange"
          color: orange
      predictions:
        enabled: true

    # Fermenter 3 - Experimental
    - name: "Experimental Sour"
      type: custom
      sensors:
        bubble_counter: "tipsylab/ferm3/bubbles"
        temperature: "tipsylab/ferm3/temp"
        ph: "tipsylab/ferm3/ph"
      predictions:
        enabled: false  # Too experimental for predictions
```

### Example 4: Research Setup with InfluxDB

```yaml
tipsyhomelab:
  mqtt:
    broker: localhost

  batches:
    - name: "Research Batch Alpha"
      type: wine
      sensors:
        bubble_counter: "tipsylab/research/bubbles"
        ispindel: "ispindel/research"
        temperature:
          - name: wort_temp
            topic: "tipsylab/research/temp/wort"
          - name: ambient_temp
            topic: "tipsylab/research/temp/ambient"
        ph: "tipsylab/research/ph"
        pressure: "tipsylab/research/pressure"

      predictions:
        enabled: true
        model: ml
        parameters:
          algorithm: gradient_boosting
          learning_rate: 0.05
          n_estimators: 200
        save_model: true

  data_storage:
    influxdb:
      enabled: true
      host: localhost
      database: research
      retention_days: 730  # 2 years

    csv_export:
      enabled: true
      path: /config/research/exports/
      interval: 3600  # Hourly

  logging:
    level: debug
    log_file: /config/research/detailed.log
```

---

## Configuration Validation

### Check Configuration

Before restarting Home Assistant, validate your configuration:

```bash
# Check all configuration
ha core check

# View configuration
ha core config
```

### Common Validation Errors

**Error**: `Invalid config for [tipsyhomelab]`
- Check YAML indentation (use spaces, not tabs)
- Verify all required fields present
- Check for typos in option names

**Error**: `MQTT broker connection failed`
- Verify broker address and port
- Check username/password
- Ensure broker is running

**Error**: `Sensor topic not found`
- Verify MQTT topic names
- Check sensors are publishing
- Test with mosquitto_sub

---

## Best Practices

1. **Use Secrets**: Store credentials in `secrets.yaml`
2. **Start Simple**: Begin with minimal config, add features gradually
3. **Test Sensors**: Verify each sensor before adding to config
4. **Backup Config**: Keep backups before major changes
5. **Version Control**: Use git for configuration.yaml
6. **Document Changes**: Add comments explaining custom settings
7. **Monitor Logs**: Check logs after config changes
8. **Validate First**: Always validate before restart

---

## Migration Guide

### Upgrading from v1.0 to v1.1

Breaking changes:
```yaml
# OLD (v1.0)
sensors:
  bubble: "topic/bubbles"

# NEW (v1.1)
sensors:
  bubble_counter: "topic/bubbles"
```

See [CHANGELOG.md](../CHANGELOG.md) for complete migration guides.

---

## Getting Help

For configuration assistance:
- Check [examples/](../examples/) directory
- Search [GitHub Discussions](https://github.com/yourusername/tipsyhomelab/discussions)
- Ask in [Discord](https://discord.gg/tipsyhomelab)
- Open an [issue](https://github.com/yourusername/tipsyhomelab/issues) with your sanitized config
