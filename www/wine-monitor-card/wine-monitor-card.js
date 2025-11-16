import { LitElement, html, css } from 'https://unpkg.com/lit-element@2.5.1/lit-element.js?module';

class WineMonitorCard extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object },
      _sensors: { type: Object }
    };
  }

  static getStubConfig() {
    return {
      name: 'Wine Monitor',
      view: 'overview',
      show_alerts: true,
      show_charts: true
    };
  }

  setConfig(config) {
    if (!config) {
      throw new Error('Invalid configuration');
    }
    this.config = config;
  }

  getCardSize() {
    const view = this.config.view || 'overview';
    switch (view) {
      case 'overview': return 3;
      case 'detail': return 8;
      case 'historical': return 6;
      case 'alerts': return 4;
      default: return 3;
    }
  }

  static get styles() {
    return css`
      :host {
        --mush-spacing: 12px;
        --mush-border-radius: 12px;
        --mush-chip-border-radius: 18px;
        --primary-text-color: var(--primary-text-color, #212121);
        --secondary-text-color: var(--secondary-text-color, #727272);
        --mush-rgb-green: 76, 175, 80;
        --mush-rgb-yellow: 255, 193, 7;
        --mush-rgb-red: 244, 67, 54;
        --mush-rgb-blue: 33, 150, 243;
        --mush-rgb-purple: 156, 39, 176;
      }

      ha-card {
        padding: 16px;
        background: var(--ha-card-background, var(--card-background-color, white));
        border-radius: var(--mush-border-radius);
        box-shadow:
          0 2px 4px rgba(0, 0, 0, 0.05),
          0 1px 2px rgba(0, 0, 0, 0.1);
        transition: box-shadow 0.3s ease;
      }

      ha-card:hover {
        box-shadow:
          0 4px 8px rgba(0, 0, 0, 0.1),
          0 2px 4px rgba(0, 0, 0, 0.15);
      }

      .card-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 16px;
        padding-bottom: 12px;
        border-bottom: 1px solid rgba(0, 0, 0, 0.05);
      }

      .card-title {
        font-size: 20px;
        font-weight: 500;
        color: var(--primary-text-color);
        display: flex;
        align-items: center;
        gap: 8px;
      }

      .card-title ha-icon {
        --mdc-icon-size: 24px;
        color: var(--mush-rgb-purple);
      }

      .status-chip {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 6px 12px;
        border-radius: var(--mush-chip-border-radius);
        font-size: 12px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        transition: all 0.2s ease;
      }

      .status-chip ha-icon {
        --mdc-icon-size: 16px;
      }

      .status-chip.fermenting {
        background: rgba(var(--mush-rgb-green), 0.15);
        color: rgb(var(--mush-rgb-green));
      }

      .status-chip.ready {
        background: rgba(var(--mush-rgb-blue), 0.15);
        color: rgb(var(--mush-rgb-blue));
      }

      .status-chip.stuck {
        background: rgba(var(--mush-rgb-red), 0.15);
        color: rgb(var(--mush-rgb-red));
      }

      .status-chip.monitoring {
        background: rgba(var(--mush-rgb-yellow), 0.15);
        color: rgb(var(--mush-rgb-yellow));
      }

      .metrics-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
        gap: 12px;
        margin-bottom: 16px;
      }

      .metric-card {
        background: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.03);
        border-radius: var(--mush-border-radius);
        padding: 12px;
        transition: all 0.2s ease;
      }

      .metric-card:hover {
        background: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.06);
        transform: translateY(-2px);
      }

      .metric-header {
        display: flex;
        align-items: center;
        gap: 8px;
        margin-bottom: 8px;
      }

      .metric-icon {
        --mdc-icon-size: 20px;
        color: var(--secondary-text-color);
      }

      .metric-label {
        font-size: 11px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--secondary-text-color);
      }

      .metric-value {
        font-size: 24px;
        font-weight: 500;
        color: var(--primary-text-color);
        line-height: 1;
        margin-bottom: 4px;
      }

      .metric-subtext {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .chart-container {
        background: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.03);
        border-radius: var(--mush-border-radius);
        padding: 16px;
        margin-bottom: 12px;
      }

      .chart-title {
        font-size: 13px;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: var(--secondary-text-color);
        margin-bottom: 12px;
      }

      .mini-chart {
        height: 80px;
        position: relative;
      }

      .alert-container {
        background: rgba(var(--mush-rgb-yellow), 0.1);
        border-left: 3px solid rgb(var(--mush-rgb-yellow));
        border-radius: var(--mush-border-radius);
        padding: 12px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 12px;
      }

      .alert-container.error {
        background: rgba(var(--mush-rgb-red), 0.1);
        border-left-color: rgb(var(--mush-rgb-red));
      }

      .alert-container.success {
        background: rgba(var(--mush-rgb-green), 0.1);
        border-left-color: rgb(var(--mush-rgb-green));
      }

      .alert-icon {
        --mdc-icon-size: 24px;
        color: rgb(var(--mush-rgb-yellow));
      }

      .alert-container.error .alert-icon {
        color: rgb(var(--mush-rgb-red));
      }

      .alert-container.success .alert-icon {
        color: rgb(var(--mush-rgb-green));
      }

      .alert-message {
        flex: 1;
        font-size: 13px;
        color: var(--primary-text-color);
      }

      .section-divider {
        height: 1px;
        background: rgba(0, 0, 0, 0.05);
        margin: 16px 0;
      }

      .sensor-unavailable {
        opacity: 0.5;
        pointer-events: none;
      }

      .gauge-container {
        position: relative;
        width: 120px;
        height: 120px;
        margin: 0 auto;
      }

      .progress-ring {
        transform: rotate(-90deg);
      }

      .progress-ring-circle {
        stroke: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.1);
        fill: transparent;
        stroke-width: 8;
      }

      .progress-ring-fill {
        stroke: rgb(var(--mush-rgb-green));
        fill: transparent;
        stroke-width: 8;
        stroke-linecap: round;
        transition: stroke-dashoffset 0.5s ease;
      }

      .gauge-value {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        text-align: center;
      }

      .gauge-value-number {
        font-size: 24px;
        font-weight: 600;
        color: var(--primary-text-color);
      }

      .gauge-value-unit {
        font-size: 12px;
        color: var(--secondary-text-color);
      }

      .trend-indicator {
        display: inline-flex;
        align-items: center;
        gap: 4px;
        font-size: 12px;
        font-weight: 500;
      }

      .trend-indicator.up {
        color: rgb(var(--mush-rgb-green));
      }

      .trend-indicator.down {
        color: rgb(var(--mush-rgb-red));
      }

      .trend-indicator.stable {
        color: var(--secondary-text-color);
      }

      .trend-indicator ha-icon {
        --mdc-icon-size: 14px;
      }

      @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.5; }
      }

      .pulsing {
        animation: pulse 2s ease-in-out infinite;
      }
    `;
  }

  _getSensors() {
    if (!this.hass) return {};

    const sensors = {
      // Core sensors (always available)
      bubble_rate: this.hass.states['sensor.wine_bubble_rate'],
      status: this.hass.states['sensor.wine_fermentation_status'],
      bottling: this.hass.states['sensor.wine_bottling_prediction'],

      // Optional sensors
      gravity: this.hass.states['sensor.wine_gravity'],
      battery: this.hass.states['sensor.wine_battery'],
      tilt: this.hass.states['sensor.wine_tilt'],
      temperature: this.hass.states['sensor.wine_temperature'],
      ph: this.hass.states['sensor.wine_ph'],
      mlf_status: this.hass.states['sensor.wine_mlf_status'],
      pressure: this.hass.states['sensor.wine_pressure'],
      abv: this.hass.states['sensor.wine_abv'],
      days_fermenting: this.hass.states['sensor.wine_days_fermenting']
    };

    return sensors;
  }

  _getStatusChipType(status) {
    if (!status) return 'monitoring';
    const state = status.state.toLowerCase();

    if (state.includes('fermenting') || state.includes('active')) return 'fermenting';
    if (state.includes('ready') || state.includes('complete')) return 'ready';
    if (state.includes('stuck') || state.includes('error')) return 'stuck';
    return 'monitoring';
  }

  _getTrendIndicator(sensor, attribute = 'trend') {
    if (!sensor || !sensor.attributes || !sensor.attributes[attribute]) {
      return html`<span class="trend-indicator stable">
        <ha-icon icon="mdi:minus"></ha-icon>
      </span>`;
    }

    const trend = sensor.attributes[attribute];
    if (trend > 0.1) {
      return html`<span class="trend-indicator up">
        <ha-icon icon="mdi:trending-up"></ha-icon>
        ${Math.abs(trend).toFixed(1)}%
      </span>`;
    } else if (trend < -0.1) {
      return html`<span class="trend-indicator down">
        <ha-icon icon="mdi:trending-down"></ha-icon>
        ${Math.abs(trend).toFixed(1)}%
      </span>`;
    } else {
      return html`<span class="trend-indicator stable">
        <ha-icon icon="mdi:minus"></ha-icon>
        Stable
      </span>`;
    }
  }

  _renderOverviewView() {
    const sensors = this._getSensors();
    const status = sensors.status;
    const chipType = this._getStatusChipType(status);

    return html`
      <div class="card-header">
        <div class="card-title">
          <ha-icon icon="mdi:glass-wine"></ha-icon>
          ${this.config.name || 'Wine Monitor'}
        </div>
        ${status ? html`
          <div class="status-chip ${chipType}">
            <ha-icon icon="${this._getStatusIcon(chipType)}"></ha-icon>
            ${status.state}
          </div>
        ` : ''}
      </div>

      ${this._renderAlerts(sensors)}

      <div class="metrics-grid">
        <!-- Bubble Rate (Always shown) -->
        ${sensors.bubble_rate ? html`
          <div class="metric-card ${sensors.bubble_rate.state === 'unavailable' ? 'sensor-unavailable' : ''}">
            <div class="metric-header">
              <ha-icon class="metric-icon ${chipType === 'fermenting' ? 'pulsing' : ''}" icon="mdi:water"></ha-icon>
              <span class="metric-label">Bubble Rate</span>
            </div>
            <div class="metric-value">${sensors.bubble_rate.state}</div>
            <div class="metric-subtext">bubbles/min</div>
          </div>
        ` : ''}

        <!-- Days Fermenting (Always shown) -->
        ${sensors.days_fermenting ? html`
          <div class="metric-card">
            <div class="metric-header">
              <ha-icon class="metric-icon" icon="mdi:calendar-clock"></ha-icon>
              <span class="metric-label">Fermenting</span>
            </div>
            <div class="metric-value">${sensors.days_fermenting.state}</div>
            <div class="metric-subtext">days</div>
          </div>
        ` : ''}

        <!-- Bottling Prediction (Always shown) -->
        ${sensors.bottling ? html`
          <div class="metric-card">
            <div class="metric-header">
              <ha-icon class="metric-icon" icon="mdi:bottle-wine"></ha-icon>
              <span class="metric-label">Bottling</span>
            </div>
            <div class="metric-value">${sensors.bottling.state}</div>
            <div class="metric-subtext">days remaining</div>
          </div>
        ` : ''}

        <!-- Gravity (if iSpindel) -->
        ${sensors.gravity && sensors.gravity.state !== 'unavailable' ? html`
          <div class="metric-card">
            <div class="metric-header">
              <ha-icon class="metric-icon" icon="mdi:gauge"></ha-icon>
              <span class="metric-label">Gravity</span>
            </div>
            <div class="metric-value">${parseFloat(sensors.gravity.state).toFixed(3)}</div>
            <div class="metric-subtext">
              ${this._getTrendIndicator(sensors.gravity)}
            </div>
          </div>
        ` : ''}

        <!-- Temperature (if available) -->
        ${sensors.temperature && sensors.temperature.state !== 'unavailable' ? html`
          <div class="metric-card">
            <div class="metric-header">
              <ha-icon class="metric-icon" icon="mdi:thermometer"></ha-icon>
              <span class="metric-label">Temperature</span>
            </div>
            <div class="metric-value">${parseFloat(sensors.temperature.state).toFixed(1)}</div>
            <div class="metric-subtext">°${sensors.temperature.attributes.unit_of_measurement || 'C'}</div>
          </div>
        ` : ''}

        <!-- ABV (if calculated) -->
        ${sensors.abv && sensors.abv.state !== 'unavailable' ? html`
          <div class="metric-card">
            <div class="metric-header">
              <ha-icon class="metric-icon" icon="mdi:percent"></ha-icon>
              <span class="metric-label">ABV</span>
            </div>
            <div class="metric-value">${parseFloat(sensors.abv.state).toFixed(1)}</div>
            <div class="metric-subtext">% alcohol</div>
          </div>
        ` : ''}
      </div>

      ${this._renderConditionalSections(sensors)}
    `;
  }

  _renderConditionalSections(sensors) {
    return html`
      <!-- iSpindel Section -->
      ${sensors.battery && sensors.battery.state !== 'unavailable' ? html`
        <div class="section-divider"></div>
        <div class="chart-container">
          <div class="chart-title">iSpindel Status</div>
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-header">
                <ha-icon class="metric-icon" icon="mdi:battery"></ha-icon>
                <span class="metric-label">Battery</span>
              </div>
              <div class="metric-value">${sensors.battery.state}</div>
              <div class="metric-subtext">%</div>
            </div>
            ${sensors.tilt ? html`
              <div class="metric-card">
                <div class="metric-header">
                  <ha-icon class="metric-icon" icon="mdi:angle-acute"></ha-icon>
                  <span class="metric-label">Tilt</span>
                </div>
                <div class="metric-value">${parseFloat(sensors.tilt.state).toFixed(1)}</div>
                <div class="metric-subtext">degrees</div>
              </div>
            ` : ''}
          </div>
        </div>
      ` : ''}

      <!-- pH Section -->
      ${sensors.ph && sensors.ph.state !== 'unavailable' ? html`
        <div class="section-divider"></div>
        <div class="chart-container">
          <div class="chart-title">pH Monitoring</div>
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-header">
                <ha-icon class="metric-icon" icon="mdi:ph"></ha-icon>
                <span class="metric-label">pH Level</span>
              </div>
              <div class="metric-value">${parseFloat(sensors.ph.state).toFixed(2)}</div>
              <div class="metric-subtext">
                ${this._getTrendIndicator(sensors.ph)}
              </div>
            </div>
            ${sensors.mlf_status ? html`
              <div class="metric-card">
                <div class="metric-header">
                  <ha-icon class="metric-icon" icon="mdi:bacteria"></ha-icon>
                  <span class="metric-label">MLF Status</span>
                </div>
                <div class="metric-value">${sensors.mlf_status.state}</div>
              </div>
            ` : ''}
          </div>
        </div>
      ` : ''}

      <!-- Pressure Section -->
      ${sensors.pressure && sensors.pressure.state !== 'unavailable' ? html`
        <div class="section-divider"></div>
        <div class="chart-container">
          <div class="chart-title">Pressure Monitoring</div>
          ${this._renderPressureGauge(sensors.pressure)}
        </div>
      ` : ''}
    `;
  }

  _renderPressureGauge(pressureSensor) {
    if (!pressureSensor) return '';

    const pressure = parseFloat(pressureSensor.state) || 0;
    const maxPressure = 15; // PSI
    const percentage = Math.min((pressure / maxPressure) * 100, 100);
    const circumference = 2 * Math.PI * 50;
    const offset = circumference - (percentage / 100) * circumference;

    return html`
      <div class="gauge-container">
        <svg class="progress-ring" width="120" height="120">
          <circle class="progress-ring-circle" cx="60" cy="60" r="50"></circle>
          <circle
            class="progress-ring-fill"
            cx="60"
            cy="60"
            r="50"
            stroke-dasharray="${circumference}"
            stroke-dashoffset="${offset}"
          ></circle>
        </svg>
        <div class="gauge-value">
          <div class="gauge-value-number">${pressure.toFixed(1)}</div>
          <div class="gauge-value-unit">PSI</div>
        </div>
      </div>
    `;
  }

  _renderAlerts(sensors) {
    const alerts = [];

    // Check for stuck fermentation
    if (sensors.status && sensors.status.state.toLowerCase().includes('stuck')) {
      alerts.push({
        type: 'error',
        icon: 'mdi:alert-circle',
        message: 'Fermentation appears to be stuck. Check temperature and yeast health.'
      });
    }

    // Check low battery
    if (sensors.battery && parseFloat(sensors.battery.state) < 20) {
      alerts.push({
        type: 'warning',
        icon: 'mdi:battery-low',
        message: 'iSpindel battery low. Consider recharging soon.'
      });
    }

    // Check temperature
    if (sensors.temperature) {
      const temp = parseFloat(sensors.temperature.state);
      if (temp < 15 || temp > 30) {
        alerts.push({
          type: 'warning',
          icon: 'mdi:thermometer-alert',
          message: 'Temperature outside optimal range (15-30°C).'
        });
      }
    }

    // Check if ready to bottle
    if (sensors.status && sensors.status.state.toLowerCase().includes('ready')) {
      alerts.push({
        type: 'success',
        icon: 'mdi:check-circle',
        message: 'Fermentation complete! Ready to bottle.'
      });
    }

    if (!this.config.show_alerts || alerts.length === 0) return '';

    return html`
      ${alerts.map(alert => html`
        <div class="alert-container ${alert.type}">
          <ha-icon class="alert-icon" icon="${alert.icon}"></ha-icon>
          <div class="alert-message">${alert.message}</div>
        </div>
      `)}
    `;
  }

  _renderDetailView() {
    const sensors = this._getSensors();

    return html`
      <div class="card-header">
        <div class="card-title">
          <ha-icon icon="mdi:chart-line"></ha-icon>
          Detailed Metrics
        </div>
      </div>

      ${this._renderAlerts(sensors)}

      <!-- All available metrics -->
      <div class="metrics-grid">
        ${Object.entries(sensors).map(([key, sensor]) => {
          if (!sensor || sensor.state === 'unavailable') return '';

          return html`
            <div class="metric-card">
              <div class="metric-header">
                <ha-icon class="metric-icon" icon="${this._getSensorIcon(key)}"></ha-icon>
                <span class="metric-label">${this._getSensorLabel(key)}</span>
              </div>
              <div class="metric-value">${this._formatSensorValue(sensor)}</div>
              <div class="metric-subtext">
                ${sensor.attributes.unit_of_measurement || ''}
                ${this._getTrendIndicator(sensor)}
              </div>
            </div>
          `;
        })}
      </div>

      ${this.config.show_charts ? html`
        <div class="section-divider"></div>
        ${this._renderCharts(sensors)}
      ` : ''}
    `;
  }

  _renderCharts(sensors) {
    // Placeholder for chart rendering
    // In production, integrate with chart library like ApexCharts or Chart.js
    return html`
      <div class="chart-container">
        <div class="chart-title">Fermentation Timeline</div>
        <div class="mini-chart">
          <div style="text-align: center; padding: 20px; color: var(--secondary-text-color);">
            Chart integration placeholder - integrate with ApexCharts or Chart.js
          </div>
        </div>
      </div>
    `;
  }

  _renderHistoricalView() {
    return html`
      <div class="card-header">
        <div class="card-title">
          <ha-icon icon="mdi:history"></ha-icon>
          Historical Batches
        </div>
      </div>

      <div style="text-align: center; padding: 40px; color: var(--secondary-text-color);">
        Historical batch comparison view - Coming soon
      </div>
    `;
  }

  _renderAlertsView() {
    const sensors = this._getSensors();

    return html`
      <div class="card-header">
        <div class="card-title">
          <ha-icon icon="mdi:bell"></ha-icon>
          Alerts & Notifications
        </div>
      </div>

      ${this._renderAlerts(sensors)}

      <div class="chart-container">
        <div class="chart-title">Anomaly Detection</div>
        <div style="text-align: center; padding: 20px; color: var(--secondary-text-color);">
          AI-powered anomaly detection - Coming soon
        </div>
      </div>
    `;
  }

  _getStatusIcon(type) {
    switch (type) {
      case 'fermenting': return 'mdi:water';
      case 'ready': return 'mdi:check-circle';
      case 'stuck': return 'mdi:alert-circle';
      default: return 'mdi:information';
    }
  }

  _getSensorIcon(sensorKey) {
    const icons = {
      bubble_rate: 'mdi:water',
      status: 'mdi:information',
      bottling: 'mdi:bottle-wine',
      gravity: 'mdi:gauge',
      battery: 'mdi:battery',
      tilt: 'mdi:angle-acute',
      temperature: 'mdi:thermometer',
      ph: 'mdi:ph',
      mlf_status: 'mdi:bacteria',
      pressure: 'mdi:gauge-full',
      abv: 'mdi:percent',
      days_fermenting: 'mdi:calendar-clock'
    };
    return icons[sensorKey] || 'mdi:chart-line';
  }

  _getSensorLabel(sensorKey) {
    const labels = {
      bubble_rate: 'Bubble Rate',
      status: 'Status',
      bottling: 'Bottling',
      gravity: 'Gravity',
      battery: 'Battery',
      tilt: 'Tilt',
      temperature: 'Temperature',
      ph: 'pH Level',
      mlf_status: 'MLF Status',
      pressure: 'Pressure',
      abv: 'ABV',
      days_fermenting: 'Days Fermenting'
    };
    return labels[sensorKey] || sensorKey.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  }

  _formatSensorValue(sensor) {
    if (!sensor) return 'N/A';
    const value = sensor.state;

    if (isNaN(value)) return value;

    const num = parseFloat(value);
    if (num % 1 === 0) return num.toString();
    if (num < 1) return num.toFixed(3);
    if (num < 10) return num.toFixed(2);
    return num.toFixed(1);
  }

  render() {
    if (!this.hass || !this.config) {
      return html``;
    }

    const view = this.config.view || 'overview';

    let content;
    switch (view) {
      case 'detail':
        content = this._renderDetailView();
        break;
      case 'historical':
        content = this._renderHistoricalView();
        break;
      case 'alerts':
        content = this._renderAlertsView();
        break;
      default:
        content = this._renderOverviewView();
    }

    return html`
      <ha-card>
        ${content}
      </ha-card>
    `;
  }
}

customElements.define('wine-monitor-card', WineMonitorCard);

// Register card with Home Assistant
window.customCards = window.customCards || [];
window.customCards.push({
  type: 'wine-monitor-card',
  name: 'Wine Monitor Card',
  description: 'A beautiful Mushroom-style card for monitoring wine fermentation',
  preview: true,
  documentationURL: 'https://github.com/yourusername/wine-monitor-card'
});

console.info(
  '%c WINE-MONITOR-CARD %c v1.0.0 ',
  'color: white; background: #9c27b0; font-weight: 700;',
  'color: #9c27b0; background: white; font-weight: 700;'
);
