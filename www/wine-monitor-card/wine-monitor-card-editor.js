import { LitElement, html, css } from 'https://unpkg.com/lit-element@2.5.1/lit-element.js?module';

class WineMonitorCardEditor extends LitElement {
  static get properties() {
    return {
      hass: { type: Object },
      config: { type: Object }
    };
  }

  setConfig(config) {
    this.config = config;
  }

  static get styles() {
    return css`
      :host {
        display: block;
      }

      .config-section {
        margin-bottom: 16px;
        padding: 12px;
        background: var(--secondary-background-color);
        border-radius: 8px;
      }

      .config-header {
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 12px;
        color: var(--primary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }

      .config-row {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
      }

      .config-row:last-child {
        margin-bottom: 0;
      }

      .config-label {
        flex: 1;
        font-size: 14px;
        color: var(--primary-text-color);
      }

      .config-input {
        flex: 2;
      }

      ha-textfield {
        width: 100%;
      }

      ha-select {
        width: 100%;
      }

      ha-switch {
        padding: 8px;
      }

      .help-text {
        font-size: 12px;
        color: var(--secondary-text-color);
        margin-top: 4px;
        font-style: italic;
      }

      .preview-section {
        margin-top: 16px;
        padding: 12px;
        background: var(--primary-background-color);
        border-radius: 8px;
        border: 1px solid var(--divider-color);
      }

      .preview-header {
        font-size: 12px;
        font-weight: 500;
        margin-bottom: 8px;
        color: var(--secondary-text-color);
        text-transform: uppercase;
        letter-spacing: 0.5px;
      }
    `;
  }

  render() {
    if (!this.config) {
      return html``;
    }

    return html`
      <div class="config-section">
        <div class="config-header">General Settings</div>

        <div class="config-row">
          <div class="config-label">Card Name</div>
          <div class="config-input">
            <ha-textfield
              .label=${'Name'}
              .value=${this.config.name || 'Wine Monitor'}
              .configValue=${'name'}
              @input=${this._valueChanged}
            ></ha-textfield>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">View Type</div>
          <div class="config-input">
            <ha-select
              .label=${'View'}
              .value=${this.config.view || 'overview'}
              .configValue=${'view'}
              @selected=${this._valueChanged}
              @closed=${(e) => e.stopPropagation()}
            >
              <mwc-list-item value="overview">Overview</mwc-list-item>
              <mwc-list-item value="detail">Detailed Metrics</mwc-list-item>
              <mwc-list-item value="historical">Historical Batches</mwc-list-item>
              <mwc-list-item value="alerts">Alerts & Notifications</mwc-list-item>
            </ha-select>
            <div class="help-text">Choose the default view for this card</div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-header">Display Options</div>

        <div class="config-row">
          <div class="config-label">Show Alerts</div>
          <div class="config-input">
            <ha-switch
              .checked=${this.config.show_alerts !== false}
              .configValue=${'show_alerts'}
              @change=${this._toggleChanged}
            ></ha-switch>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Show Charts</div>
          <div class="config-input">
            <ha-switch
              .checked=${this.config.show_charts !== false}
              .configValue=${'show_charts'}
              @change=${this._toggleChanged}
            ></ha-switch>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Compact Mode</div>
          <div class="config-input">
            <ha-switch
              .checked=${this.config.compact_mode === true}
              .configValue=${'compact_mode'}
              @change=${this._toggleChanged}
            ></ha-switch>
            <div class="help-text">Reduce spacing and padding for smaller displays</div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-header">Sensor Configuration</div>

        <div class="config-row">
          <div class="config-label">Entity Prefix</div>
          <div class="config-input">
            <ha-textfield
              .label=${'Prefix'}
              .value=${this.config.entity_prefix || 'wine'}
              .configValue=${'entity_prefix'}
              @input=${this._valueChanged}
            ></ha-textfield>
            <div class="help-text">
              Sensor entity prefix (e.g., 'wine' for sensor.wine_bubble_rate)
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-header">Alert Thresholds</div>

        <div class="config-row">
          <div class="config-label">Low Battery Warning (%)</div>
          <div class="config-input">
            <ha-textfield
              type="number"
              .label=${'Battery %'}
              .value=${this.config.battery_threshold || '20'}
              .configValue=${'battery_threshold'}
              @input=${this._valueChanged}
              min="0"
              max="100"
            ></ha-textfield>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Min Temperature (°C)</div>
          <div class="config-input">
            <ha-textfield
              type="number"
              .label=${'Min Temp'}
              .value=${this.config.temp_min || '15'}
              .configValue=${'temp_min'}
              @input=${this._valueChanged}
            ></ha-textfield>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Max Temperature (°C)</div>
          <div class="config-input">
            <ha-textfield
              type="number"
              .label=${'Max Temp'}
              .value=${this.config.temp_max || '30'}
              .configValue=${'temp_max'}
              @input=${this._valueChanged}
            ></ha-textfield>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Stuck Fermentation Threshold (hours)</div>
          <div class="config-input">
            <ha-textfield
              type="number"
              .label=${'Hours'}
              .value=${this.config.stuck_threshold || '24'}
              .configValue=${'stuck_threshold'}
              @input=${this._valueChanged}
            ></ha-textfield>
            <div class="help-text">
              Alert if no activity detected for this many hours
            </div>
          </div>
        </div>
      </div>

      <div class="config-section">
        <div class="config-header">Advanced Options</div>

        <div class="config-row">
          <div class="config-label">Update Interval (seconds)</div>
          <div class="config-input">
            <ha-textfield
              type="number"
              .label=${'Interval'}
              .value=${this.config.update_interval || '60'}
              .configValue=${'update_interval'}
              @input=${this._valueChanged}
              min="10"
            ></ha-textfield>
            <div class="help-text">
              How often to refresh sensor data
            </div>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Enable Animations</div>
          <div class="config-input">
            <ha-switch
              .checked=${this.config.enable_animations !== false}
              .configValue=${'enable_animations'}
              @change=${this._toggleChanged}
            ></ha-switch>
          </div>
        </div>

        <div class="config-row">
          <div class="config-label">Debug Mode</div>
          <div class="config-input">
            <ha-switch
              .checked=${this.config.debug === true}
              .configValue=${'debug'}
              @change=${this._toggleChanged}
            ></ha-switch>
            <div class="help-text">
              Show additional debug information in browser console
            </div>
          </div>
        </div>
      </div>

      <div class="preview-section">
        <div class="preview-header">Configuration Preview</div>
        <pre style="font-size: 11px; overflow-x: auto;">${JSON.stringify(this.config, null, 2)}</pre>
      </div>
    `;
  }

  _valueChanged(ev) {
    if (!this.config || !this.hass) {
      return;
    }

    const target = ev.target;
    const configValue = target.configValue;

    if (this[`_${configValue}`] === target.value) {
      return;
    }

    if (target.value === '') {
      const newConfig = { ...this.config };
      delete newConfig[configValue];
      this.config = newConfig;
    } else {
      this.config = {
        ...this.config,
        [configValue]: target.value
      };
    }

    this._fireEvent();
  }

  _toggleChanged(ev) {
    if (!this.config || !this.hass) {
      return;
    }

    const target = ev.target;
    const configValue = target.configValue;

    this.config = {
      ...this.config,
      [configValue]: target.checked
    };

    this._fireEvent();
  }

  _fireEvent() {
    const event = new Event('config-changed', {
      bubbles: true,
      composed: true
    });
    event.detail = { config: this.config };
    this.dispatchEvent(event);
  }
}

customElements.define('wine-monitor-card-editor', WineMonitorCardEditor);
