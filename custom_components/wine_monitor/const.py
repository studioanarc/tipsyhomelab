"""Constants for the Wine Monitor integration."""

DOMAIN = "wine_monitor"
NAME = "Wine Monitor"
VERSION = "1.0.0"

# Configuration
CONF_API_URL = "api_url"
CONF_WEBHOOK_ID = "webhook_id"
CONF_UPDATE_INTERVAL = "update_interval"

# Default values
DEFAULT_UPDATE_INTERVAL = 60  # seconds
DEFAULT_NAME = "Wine Fermentation"

# Sensor types
SENSOR_TYPES = {
    "bubble_rate": {
        "name": "Bubble Rate",
        "unit": "bubbles/min",
        "icon": "mdi:water",
        "device_class": None,
        "state_class": "measurement",
    },
    "fermentation_status": {
        "name": "Fermentation Status",
        "unit": None,
        "icon": "mdi:information",
        "device_class": None,
        "state_class": None,
    },
    "bottling_prediction": {
        "name": "Days to Bottling",
        "unit": "days",
        "icon": "mdi:bottle-wine",
        "device_class": None,
        "state_class": "measurement",
    },
    "gravity": {
        "name": "Specific Gravity",
        "unit": "SG",
        "icon": "mdi:gauge",
        "device_class": None,
        "state_class": "measurement",
    },
    "temperature": {
        "name": "Temperature",
        "unit": "°C",
        "icon": "mdi:thermometer",
        "device_class": "temperature",
        "state_class": "measurement",
    },
    "battery": {
        "name": "Battery",
        "unit": "%",
        "icon": "mdi:battery",
        "device_class": "battery",
        "state_class": "measurement",
    },
    "tilt": {
        "name": "Tilt Angle",
        "unit": "°",
        "icon": "mdi:angle-acute",
        "device_class": None,
        "state_class": "measurement",
    },
    "ph": {
        "name": "pH Level",
        "unit": "pH",
        "icon": "mdi:ph",
        "device_class": None,
        "state_class": "measurement",
    },
    "mlf_status": {
        "name": "MLF Status",
        "unit": None,
        "icon": "mdi:bacteria",
        "device_class": None,
        "state_class": None,
    },
    "pressure": {
        "name": "Pressure",
        "unit": "PSI",
        "icon": "mdi:gauge-full",
        "device_class": "pressure",
        "state_class": "measurement",
    },
    "abv": {
        "name": "Alcohol by Volume",
        "unit": "%",
        "icon": "mdi:percent",
        "device_class": None,
        "state_class": "measurement",
    },
    "days_fermenting": {
        "name": "Days Fermenting",
        "unit": "days",
        "icon": "mdi:calendar-clock",
        "device_class": None,
        "state_class": "measurement",
    },
    "og": {
        "name": "Original Gravity",
        "unit": "SG",
        "icon": "mdi:gauge",
        "device_class": None,
        "state_class": "measurement",
    },
    "fg": {
        "name": "Final Gravity",
        "unit": "SG",
        "icon": "mdi:gauge",
        "device_class": None,
        "state_class": "measurement",
    },
    "attenuation": {
        "name": "Attenuation",
        "unit": "%",
        "icon": "mdi:percent",
        "device_class": None,
        "state_class": "measurement",
    },
}

# Fermentation status states
STATUS_FERMENTING = "Fermenting"
STATUS_ACTIVE = "Active"
STATUS_READY = "Ready to Bottle"
STATUS_STUCK = "Stuck Fermentation"
STATUS_MONITORING = "Monitoring"
STATUS_COMPLETE = "Complete"

# MLF status states
MLF_NOT_STARTED = "Not Started"
MLF_IN_PROGRESS = "In Progress"
MLF_COMPLETE = "Complete"

# Alert types
ALERT_LOW_BATTERY = "low_battery"
ALERT_TEMP_OUT_OF_RANGE = "temperature_alert"
ALERT_STUCK_FERMENTATION = "stuck_fermentation"
ALERT_READY_TO_BOTTLE = "ready_to_bottle"

# Alert thresholds
BATTERY_LOW_THRESHOLD = 20  # percent
TEMP_MIN_THRESHOLD = 15  # °C
TEMP_MAX_THRESHOLD = 30  # °C
STUCK_FERMENTATION_HOURS = 24  # hours without activity

# API endpoints
ENDPOINT_STATUS = "/api/status"
ENDPOINT_SENSORS = "/api/sensors"
ENDPOINT_HISTORY = "/api/history"
ENDPOINT_ALERTS = "/api/alerts"

# Data storage
STORAGE_VERSION = 1
STORAGE_KEY = f"{DOMAIN}.storage"

# Attributes
ATTR_BATCH_ID = "batch_id"
ATTR_BATCH_NAME = "batch_name"
ATTR_START_DATE = "start_date"
ATTR_TREND = "trend"
ATTR_LAST_UPDATE = "last_update"
ATTR_SOURCE = "source"
ATTR_QUALITY = "data_quality"

# Device info
MANUFACTURER = "TipsyHomeLab"
MODEL = "Wine Monitor v1"
