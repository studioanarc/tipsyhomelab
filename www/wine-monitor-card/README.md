# Wine Monitor Card

A beautiful Mushroom-style custom Lovelace card for Home Assistant to monitor wine fermentation.

![Wine Monitor Card](../../docs/images/wine-monitor-card-preview.png)

## Features

- 🎨 **Mushroom Design Language**: Clean, modern, minimalist aesthetic
- 🔄 **Conditional UI**: Shows/hides sections based on available sensors
- 📊 **Multiple Views**: Overview, Detail, Historical, Alerts
- 📱 **Responsive**: Optimized for desktop and mobile
- ⚡ **Real-time Updates**: Live sensor data updates
- 🎭 **Smooth Animations**: Polished transitions and effects
- 🌈 **Color-coded Alerts**: Green/yellow/red status indicators
- 📈 **Trend Indicators**: See changes at a glance

## Quick Start

### 1. Installation

Copy the card files to your Home Assistant:

```bash
cp -r wine-monitor-card /config/www/
```

### 2. Add Resource

Settings → Dashboards → Resources → Add Resource

- URL: `/local/wine-monitor-card/wine-monitor-card.js`
- Type: JavaScript Module

### 3. Add to Dashboard

```yaml
type: custom:wine-monitor-card
name: My Wine Fermentation
view: overview
```

## Configuration

### Basic Configuration

```yaml
type: custom:wine-monitor-card
name: Wine Monitor
view: overview
show_alerts: true
show_charts: true
```

### Full Configuration

```yaml
type: custom:wine-monitor-card

# Display
name: "My Pinot Noir 2024"
view: overview  # overview | detail | historical | alerts
show_alerts: true
show_charts: true
compact_mode: false

# Multi-batch support
entity_prefix: wine  # Use different prefix for each batch

# Alert thresholds
battery_threshold: 20      # %
temp_min: 15              # °C
temp_max: 30              # °C
stuck_threshold: 24       # hours

# Advanced
update_interval: 60       # seconds
enable_animations: true
debug: false
```

## View Modes

### Overview (Default)

Perfect for everyday monitoring:
- Fermentation status chip
- Key metrics (bubble rate, days, bottling prediction)
- Conditional sections for available sensors
- Active alerts

### Detail

Complete sensor overview:
- All available sensors
- Trend indicators
- Charts and graphs
- Extended metrics

### Historical

Batch comparison and history:
- Previous batch data
- Performance comparisons
- Long-term trends

### Alerts

Alert management:
- Active alerts
- Alert history
- Anomaly detection

## Conditional Sections

The card intelligently shows/hides sections based on available data:

### Always Shown
- ✅ Bubble rate
- ✅ Fermentation status
- ✅ Bottling prediction
- ✅ Days fermenting

### Conditional Sections

**iSpindel** (shown if `sensor.wine_battery` exists)
- Battery level
- Tilt angle
- Signal strength

**pH Monitoring** (shown if `sensor.wine_ph` exists)
- pH level with trend
- MLF status

**Pressure** (shown if `sensor.wine_pressure` exists)
- Pressure gauge
- Visual indicator

**Temperature** (shown if `sensor.wine_temperature` exists)
- Current temperature
- Temperature trend
- Historical chart

## Alerts

Automatic alerts for:
- 🔴 **Stuck Fermentation**: No activity for threshold hours
- 🟡 **Low Battery**: iSpindel battery below threshold
- 🟡 **Temperature**: Outside optimal range
- 🟢 **Ready to Bottle**: Fermentation complete

## Multi-Batch Setup

Monitor multiple batches with different entity prefixes:

```yaml
# Batch 1: Pinot Noir
- type: custom:wine-monitor-card
  name: Pinot Noir
  entity_prefix: wine_pinot

# Batch 2: Chardonnay
- type: custom:wine-monitor-card
  name: Chardonnay
  entity_prefix: wine_chard
```

Requires sensors named:
- `sensor.wine_pinot_bubble_rate`
- `sensor.wine_chard_bubble_rate`
- etc.

## Styling

The card follows the Mushroom design language with:

- **Rounded corners**: 12px border radius
- **Soft shadows**: Subtle elevation
- **Chip-style indicators**: Rounded status badges
- **Clean typography**: Modern sans-serif
- **Smooth transitions**: 250ms ease animations
- **Color palette**: Green/yellow/red status colors

### CSS Variables

Customize in your theme:

```css
:root {
  --wine-monitor-primary: #9c27b0;
  --mush-border-radius: 12px;
  --mush-spacing: 12px;
}
```

## Browser Support

- ✅ Chrome/Edge 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Home Assistant Companion App

## Development

### File Structure

```
wine-monitor-card/
├── wine-monitor-card.js           # Main card component
├── wine-monitor-card-editor.js    # Configuration editor
├── styles.css                     # Mushroom-inspired styles
└── README.md                      # This file
```

### Technologies

- **LitElement 2.5.1**: Web components framework
- **Lit HTML**: Templating
- **CSS Variables**: Theming
- **Home Assistant**: Integration

### Debug Mode

Enable debug logging:

```yaml
type: custom:wine-monitor-card
debug: true
```

Check browser console (F12) for detailed logs.

## Troubleshooting

### Card Not Showing

1. Verify resource is added
2. Clear browser cache (`Ctrl+Shift+R`)
3. Check browser console for errors

### Sensors Missing

This is normal! Sensors appear only if data is available.

Check available sensors:
```
Developer Tools → States → filter "wine_"
```

### Styling Issues

1. Clear browser cache
2. Check theme compatibility
3. Verify CSS file is loaded

## Examples

See `/examples/lovelace-dashboards.yaml` for complete examples.

## License

MIT License - See LICENSE file

## Credits

- Inspired by [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- Built for [TipsyHomeLab](https://github.com/tipsyhomelab/wine-monitor)

## Support

- Issues: https://github.com/tipsyhomelab/wine-monitor/issues
- Docs: https://github.com/tipsyhomelab/wine-monitor/tree/main/docs

---

Made with 🍷 for wine enthusiasts and home fermentation geeks
