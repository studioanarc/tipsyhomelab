"""Sensor platform for Wine Monitor integration."""
from __future__ import annotations

from datetime import datetime
import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import WineMonitorDataUpdateCoordinator
from .const import (
    ATTR_BATCH_ID,
    ATTR_BATCH_NAME,
    ATTR_LAST_UPDATE,
    ATTR_SOURCE,
    ATTR_START_DATE,
    ATTR_TREND,
    DOMAIN,
    MANUFACTURER,
    MODEL,
    NAME,
    SENSOR_TYPES,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Wine Monitor sensors based on a config entry."""
    coordinator: WineMonitorDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    # Get initial data to determine available sensors
    sensor_data = coordinator.data.get("sensors", {})

    # Create sensor entities dynamically based on available data
    entities = []

    for sensor_key, sensor_config in SENSOR_TYPES.items():
        # Check if this sensor has data
        sensor_value = sensor_data.get(sensor_key)

        if sensor_value is not None:
            entities.append(
                WineMonitorSensor(
                    coordinator=coordinator,
                    sensor_key=sensor_key,
                    sensor_config=sensor_config,
                    entry=entry,
                )
            )
            _LOGGER.debug("Created sensor: wine_%s", sensor_key)
        else:
            _LOGGER.debug("Skipping sensor wine_%s (no data available)", sensor_key)

    async_add_entities(entities)


class WineMonitorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Wine Monitor Sensor."""

    def __init__(
        self,
        coordinator: WineMonitorDataUpdateCoordinator,
        sensor_key: str,
        sensor_config: dict[str, Any],
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)

        self._sensor_key = sensor_key
        self._attr_name = f"Wine {sensor_config['name']}"
        self._attr_unique_id = f"{entry.entry_id}_{sensor_key}"
        self._attr_native_unit_of_measurement = sensor_config.get("unit")
        self._attr_icon = sensor_config["icon"]
        self._attr_device_class = sensor_config.get("device_class")
        self._attr_state_class = sensor_config.get("state_class")

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
            sw_version=entry.data.get("version", "1.0.0"),
        )

    @property
    def native_value(self) -> str | float | int | None:
        """Return the state of the sensor."""
        sensor_data = self.coordinator.data.get("sensors", {})
        value = sensor_data.get(self._sensor_key)

        if value is None:
            return None

        # Handle different data types
        if isinstance(value, dict):
            # If the sensor data is a dict, get the 'value' key
            return value.get("value")

        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        sensor_data = self.coordinator.data.get("sensors", {})
        status_data = self.coordinator.data.get("status", {})

        attributes = {}

        # Get sensor-specific attributes
        sensor_value = sensor_data.get(self._sensor_key)
        if isinstance(sensor_value, dict):
            # Add all dict keys as attributes except 'value'
            for key, val in sensor_value.items():
                if key != "value":
                    attributes[key] = val

        # Add common attributes
        if ATTR_BATCH_ID in status_data:
            attributes[ATTR_BATCH_ID] = status_data[ATTR_BATCH_ID]

        if ATTR_BATCH_NAME in status_data:
            attributes[ATTR_BATCH_NAME] = status_data[ATTR_BATCH_NAME]

        if ATTR_START_DATE in status_data:
            attributes[ATTR_START_DATE] = status_data[ATTR_START_DATE]

        # Add trend information if available
        trend = self._calculate_trend()
        if trend is not None:
            attributes[ATTR_TREND] = trend

        # Add last update timestamp
        attributes[ATTR_LAST_UPDATE] = self.coordinator.data.get("timestamp")

        # Add data source
        attributes[ATTR_SOURCE] = sensor_data.get(f"{self._sensor_key}_source", "unknown")

        return attributes

    def _calculate_trend(self) -> float | None:
        """Calculate trend for the sensor (% change)."""
        # This would require historical data
        # For now, return None - implement when history API is available
        sensor_data = self.coordinator.data.get("sensors", {})
        sensor_value = sensor_data.get(self._sensor_key)

        if isinstance(sensor_value, dict) and "trend" in sensor_value:
            return sensor_value["trend"]

        return None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        if not self.coordinator.last_update_success:
            return False

        sensor_data = self.coordinator.data.get("sensors", {})
        return self._sensor_key in sensor_data


class WineMonitorBinarySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Wine Monitor Binary Sensor for alerts."""

    def __init__(
        self,
        coordinator: WineMonitorDataUpdateCoordinator,
        alert_type: str,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)

        self._alert_type = alert_type
        self._attr_name = f"Wine {alert_type.replace('_', ' ').title()}"
        self._attr_unique_id = f"{entry.entry_id}_alert_{alert_type}"
        self._attr_icon = self._get_alert_icon(alert_type)

        # Device info
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def is_on(self) -> bool:
        """Return true if alert is active."""
        status_data = self.coordinator.data.get("status", {})
        alerts = status_data.get("alerts", [])

        return any(alert.get("type") == self._alert_type for alert in alerts)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        status_data = self.coordinator.data.get("status", {})
        alerts = status_data.get("alerts", [])

        # Find alerts of this type
        matching_alerts = [
            alert for alert in alerts if alert.get("type") == self._alert_type
        ]

        if not matching_alerts:
            return {}

        # Return details of the most recent alert
        latest_alert = matching_alerts[0]

        return {
            "message": latest_alert.get("message"),
            "severity": latest_alert.get("severity"),
            "timestamp": latest_alert.get("timestamp"),
        }

    @staticmethod
    def _get_alert_icon(alert_type: str) -> str:
        """Get icon for alert type."""
        icons = {
            "low_battery": "mdi:battery-low",
            "temperature_alert": "mdi:thermometer-alert",
            "stuck_fermentation": "mdi:alert-circle",
            "ready_to_bottle": "mdi:check-circle",
        }
        return icons.get(alert_type, "mdi:alert")
