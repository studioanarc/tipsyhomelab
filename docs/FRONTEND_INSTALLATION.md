# Wine Monitor Frontend - Installation Guide

Complete installation instructions for the Wine Monitor Mushroom-style frontend components and custom Lovelace card.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installing the Custom Component](#installing-the-custom-component)
3. [Installing the Lovelace Card](#installing-the-lovelace-card)
4. [Configuration](#configuration)
5. [Dashboard Examples](#dashboard-examples)
6. [Troubleshooting](#troubleshooting)

---

## Quick Start

### What You're Installing

The Wine Monitor frontend consists of two main components:

1. **Custom Integration** (`custom_components/wine_monitor/`)
   - Creates dynamic sensors based on available data
   - Handles API communication
   - Provides Home Assistant services

2. **Lovelace Card** (`www/wine-monitor-card/`)
   - Beautiful Mushroom-style UI
   - Conditional sections based on available sensors
   - Real-time updates and visualizations

---

## Installing the Custom Component

### Prerequisites

- Home Assistant 2023.1 or newer
- Wine Monitor backend API running
- MQTT configured (optional, for real-time updates)

### Manual Installation

1. **Copy the integration files:**

   ```bash
   # From repository root
   cp -r custom_components/wine_monitor /config/custom_components/
   ```

2. **Verify file structure:**

   ```
   /config/custom_components/wine_monitor/
   ├── __init__.py
   ├── manifest.json
   ├── const.py
   ├── config_flow.py
   ├── sensor.py
   ├── services.yaml
   └── strings.json
   ```

3. **Restart Home Assistant:**

   Settings → System → Restart

4. **Add the integration:**

   - Settings → Devices & Services
   - Add Integration
   - Search "Wine Monitor"
   - Enter your API URL (e.g., `http://homeassistant.local:5000`)

### Expected Sensors

After configuration, these sensors will be created **dynamically** based on available data:

**Always Available:**
- `sensor.wine_bubble_rate` - Bubble activity
- `sensor.wine_fermentation_status` - Current status
- `sensor.wine_bottling_prediction` - Days to bottling
- `sensor.wine_days_fermenting` - Days since start

**Conditional (created only if data available):**
- `sensor.wine_gravity` - Specific gravity (iSpindel)
- `sensor.wine_battery` - Battery level (iSpindel)
- `sensor.wine_tilt` - Tilt angle (iSpindel)
- `sensor.wine_temperature` - Temperature
- `sensor.wine_ph` - pH level
- `sensor.wine_mlf_status` - Malolactic fermentation status
- `sensor.wine_pressure` - Pressure (PSI)
- `sensor.wine_abv` - Alcohol by volume

---

## Installing the Lovelace Card

### Manual Installation

1. **Copy card files:**

   ```bash
   # From repository root
   cp -r www/wine-monitor-card /config/www/
   ```

2. **Verify file structure:**

   ```
   /config/www/wine-monitor-card/
   ├── wine-monitor-card.js
   ├── wine-monitor-card-editor.js
   └── styles.css
   ```

3. **Add resource to Lovelace:**

   **Via UI (Recommended):**
   - Settings → Dashboards
   - Three dots (⋮) → Resources
   - Add Resource
   - URL: `/local/wine-monitor-card/wine-monitor-card.js`
   - Type: JavaScript Module

   **Via YAML:**
   ```yaml
   lovelace:
     resources:
       - url: /local/wine-monitor-card/wine-monitor-card.js
         type: module
   ```

4. **Clear browser cache:**

   Press `Ctrl + Shift + R` (Windows/Linux) or `Cmd + Shift + R` (Mac)

---

## Configuration

### Basic Card Setup

Add to your dashboard:

```yaml
type: custom:wine-monitor-card
name: My Wine Fermentation
view: overview
```

### All Configuration Options

```yaml
type: custom:wine-monitor-card

# Display Settings
name: string                 # Card title (default: "Wine Monitor")
view: string                 # View: overview|detail|historical|alerts (default: "overview")
show_alerts: boolean         # Show alerts (default: true)
show_charts: boolean         # Show charts (default: true)
compact_mode: boolean        # Compact layout (default: false)

# Multi-Batch Support
entity_prefix: string        # Sensor prefix (default: "wine")
                            # Example: "wine_pinot" for sensor.wine_pinot_bubble_rate

# Alert Thresholds
battery_threshold: number    # Low battery % (default: 20)
temp_min: number            # Min temp °C (default: 15)
temp_max: number            # Max temp °C (default: 30)
stuck_threshold: number     # Hours without activity (default: 24)

# Advanced
update_interval: number     # Update interval seconds (default: 60)
enable_animations: boolean  # Enable animations (default: true)
debug: boolean              # Debug logging (default: false)
```

### View Modes

**Overview** (Default)
- Status chip
- Key metrics
- Bottling prediction
- Conditional sections for available sensors

**Detail**
- All available sensors
- Trend indicators
- Charts (if enabled)

**Historical**
- Batch comparison (coming soon)
- Historical trends

**Alerts**
- Active alerts
- Anomaly detection

---

## Dashboard Examples

### Example 1: Minimal Overview

```yaml
type: custom:wine-monitor-card
name: Pinot Noir 2024
view: overview
```

### Example 2: Detailed Dashboard

```yaml
views:
  - title: Wine
    cards:
      # Main card
      - type: custom:wine-monitor-card
        name: Wine Fermentation
        view: detail
        show_charts: true

      # Gauges
      - type: horizontal-stack
        cards:
          - type: gauge
            entity: sensor.wine_temperature
            min: 10
            max: 35
            severity:
              green: 15
              yellow: 25
              red: 30

          - type: gauge
            entity: sensor.wine_gravity
            min: 0.990
            max: 1.100
```

### Example 3: Multi-Batch Setup

```yaml
# Dashboard for multiple batches
views:
  - title: Cellar
    cards:
      - type: custom:wine-monitor-card
        name: Pinot Noir
        entity_prefix: wine_pinot

      - type: custom:wine-monitor-card
        name: Chardonnay
        entity_prefix: wine_chard

      - type: custom:wine-monitor-card
        name: Cabernet
        entity_prefix: wine_cab
```

### Example 4: Mobile Compact

```yaml
type: custom:wine-monitor-card
name: Wine
view: overview
compact_mode: true
show_charts: false
```

See `/examples/lovelace-dashboards.yaml` for more examples.

---

## Conditional UI Behavior

The card automatically shows/hides sections based on available sensors:

### Always Shown
- Bubble rate
- Fermentation status
- Bottling prediction
- Days fermenting

### Shown if Available
- **iSpindel Section**: If `sensor.wine_battery` exists
  - Battery level
  - Tilt angle

- **pH Section**: If `sensor.wine_ph` exists
  - pH level with trends
  - MLF status (if available)

- **Pressure Section**: If `sensor.wine_pressure` exists
  - Pressure gauge

- **Temperature**: If `sensor.wine_temperature` exists
  - Temperature metric
  - Temperature chart (if charts enabled)

### Alert Conditions

Alerts appear automatically when:
- Fermentation is stuck (no activity for `stuck_threshold` hours)
- Battery below `battery_threshold`%
- Temperature outside `temp_min` to `temp_max` range
- Fermentation complete (ready to bottle)

---

## Troubleshooting

### Card Not Showing

**Error**: "Custom element doesn't exist: wine-monitor-card"

**Solution**:
1. Verify resource is added (Settings → Dashboards → Resources)
2. Check resource URL: `/local/wine-monitor-card/wine-monitor-card.js`
3. Ensure type is "JavaScript Module"
4. Clear browser cache: `Ctrl + Shift + R`
5. Check browser console (F12) for errors

### Sensors Not Appearing

**Issue**: Some sensors missing

**This is normal!** Sensors are created dynamically. If you don't have an iSpindel, you won't see gravity/battery/tilt sensors.

**To verify**:
1. Check available sensors: Developer Tools → States → filter `sensor.wine_`
2. Check API response: `curl http://your-api/api/sensors`
3. Review integration logs: Settings → System → Logs → filter "wine_monitor"

### Card Shows "Unavailable"

**Solutions**:
1. Verify Wine Monitor integration is configured
2. Check API is running: `curl http://your-api/api/status`
3. Review integration configuration: Settings → Devices & Services → Wine Monitor
4. Check integration logs for errors

### Empty Sections

If sections appear empty:
- Check sensor values in Developer Tools → States
- Ensure sensors have valid data (not "unknown" or "unavailable")
- Verify API is returning sensor data

### Styling Issues

If colors/styling look wrong:
1. Check if custom themes are interfering
2. Verify `styles.css` is in `/config/www/wine-monitor-card/`
3. Try default Home Assistant theme
4. Clear browser cache completely

---

## Advanced Configuration

### Custom CSS Variables

Override Mushroom styles in your theme:

```yaml
# In your theme YAML
wine-monitor-custom:
  # Change primary color
  mush-rgb-purple: 156, 39, 176

  # Adjust border radius
  mush-border-radius: 16px

  # Custom spacing
  mush-spacing: 16px
```

### Services

The integration provides these services:

#### wine_monitor.get_history

```yaml
service: wine_monitor.get_history
data:
  sensor_type: bubble_rate
  hours: 24
```

#### wine_monitor.get_alerts

```yaml
service: wine_monitor.get_alerts
```

#### wine_monitor.refresh_data

```yaml
service: wine_monitor.refresh_data
```

---

## Integration with Automations

See `/examples/automations.yaml` for complete automation examples.

### Quick Examples

**Alert when ready to bottle:**

```yaml
- alias: Wine Ready
  trigger:
    - platform: state
      entity_id: sensor.wine_fermentation_status
      to: "Ready to Bottle"
  action:
    - service: notify.mobile_app
      data:
        title: "🍷 Ready to Bottle!"
        message: "ABV: {{ states('sensor.wine_abv') }}%"
```

**Low battery warning:**

```yaml
- alias: Low Battery
  trigger:
    - platform: numeric_state
      entity_id: sensor.wine_battery
      below: 20
  action:
    - service: notify.mobile_app
      data:
        title: "🔋 Low Battery"
        message: "iSpindel at {{ states('sensor.wine_battery') }}%"
```

---

## Next Steps

After installation:

1. ✅ Verify all sensors are created
2. ✅ Set up your dashboard layout
3. ✅ Configure alert automations
4. ✅ Customize thresholds for your wine style
5. ✅ Explore different view modes

---

## Support

- **Issues**: https://github.com/tipsyhomelab/wine-monitor/issues
- **Documentation**: `/docs/` in repository
- **Examples**: `/examples/` in repository

Enjoy your beautiful wine monitoring dashboard! 🍷
