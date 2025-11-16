"""Validation schemas for wine monitor integration."""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import voluptuous as vol


# Constants for validation
MIN_TEMPERATURE = -10.0  # Celsius
MAX_TEMPERATURE = 50.0   # Celsius
MIN_GRAVITY = 0.990
MAX_GRAVITY = 1.150
MIN_BATTERY = 0.0
MAX_BATTERY = 5.0
MIN_ANGLE = 0.0
MAX_ANGLE = 90.0
MIN_RSSI = -100
MAX_RSSI = 0


class ValidationError(Exception):
    """Custom validation error."""

    pass


# Config validation schema
CONFIG_SCHEMA = vol.Schema({
    vol.Required("mqtt_broker"): str,
    vol.Optional("mqtt_port", default=1883): vol.All(int, vol.Range(min=1, max=65535)),
    vol.Optional("mqtt_username"): str,
    vol.Optional("mqtt_password"): str,
    vol.Required("ispindel_topic"): str,
    vol.Required("bubble_sensor_topic"): str,
    vol.Optional("database_url"): str,
    vol.Optional("ml_model_path"): str,
    vol.Optional("update_interval", default=900): vol.All(int, vol.Range(min=60, max=7200)),
    vol.Optional("enable_predictions", default=True): bool,
    vol.Optional("retention_days", default=365): vol.All(int, vol.Range(min=1, max=3650)),
})


# iSpindel message validation schema
ISPINDEL_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("name"): str,
    vol.Optional("ID"): str,
    vol.Optional("token"): str,
    vol.Required("angle"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_ANGLE, max=MAX_ANGLE)
    ),
    vol.Required("temperature"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_TEMPERATURE, max=MAX_TEMPERATURE)
    ),
    vol.Optional("temp_units", default="C"): vol.In(["C", "F"]),
    vol.Required("battery"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_BATTERY, max=MAX_BATTERY)
    ),
    vol.Required("gravity"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_GRAVITY, max=MAX_GRAVITY)
    ),
    vol.Optional("interval"): vol.All(int, vol.Range(min=60, max=7200)),
    vol.Optional("RSSI"): vol.All(int, vol.Range(min=MIN_RSSI, max=MAX_RSSI)),
}, extra=vol.ALLOW_EXTRA)


# Bubble sensor message validation schema
BUBBLE_SENSOR_MESSAGE_SCHEMA = vol.Schema({
    vol.Required("sensor_id"): str,
    vol.Required("timestamp"): str,  # ISO format
    vol.Required("bubble_count"): vol.All(int, vol.Range(min=0)),
    vol.Required("interval_seconds"): vol.All(int, vol.Range(min=1, max=3600)),
    vol.Required("bubble_rate_per_minute"): vol.All(
        vol.Coerce(float),
        vol.Range(min=0)
    ),
    vol.Optional("battery_percent"): vol.All(
        int,
        vol.Range(min=0, max=100)
    ),
    vol.Optional("signal_strength"): vol.All(
        int,
        vol.Range(min=MIN_RSSI, max=MAX_RSSI)
    ),
}, extra=vol.ALLOW_EXTRA)


# Batch configuration schema
BATCH_SCHEMA = vol.Schema({
    vol.Required("batch_id"): str,
    vol.Required("batch_name"): str,
    vol.Required("start_date"): str,  # ISO format
    vol.Optional("end_date"): vol.Any(str, None),
    vol.Required("initial_gravity"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_GRAVITY, max=MAX_GRAVITY)
    ),
    vol.Optional("final_gravity"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_GRAVITY, max=MAX_GRAVITY)
    ),
    vol.Optional("target_gravity"): vol.All(
        vol.Coerce(float),
        vol.Range(min=MIN_GRAVITY, max=MAX_GRAVITY)
    ),
    vol.Optional("status", default="active"): vol.In([
        "active", "completed", "cancelled", "error"
    ]),
})


class ConfigValidator:
    """Validates configuration data."""

    @staticmethod
    def validate(config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate configuration."""
        try:
            return CONFIG_SCHEMA(config)
        except vol.Error as e:
            raise ValidationError(f"Invalid configuration: {e}") from e

    @staticmethod
    def validate_mqtt_topic(topic: str) -> bool:
        """Validate MQTT topic format."""
        if not topic or len(topic) > 255:
            return False

        # Check for invalid characters
        invalid_chars = ['\0', '+', '#']
        for char in invalid_chars:
            if char in topic and topic.count(char) > 1:
                return False

        # Topic levels
        levels = topic.split('/')
        if len(levels) > 127:
            return False

        return True


class SensorDataValidator:
    """Validates sensor data."""

    @staticmethod
    def validate_ispindel(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate iSpindel message."""
        try:
            return ISPINDEL_MESSAGE_SCHEMA(data)
        except vol.Error as e:
            raise ValidationError(f"Invalid iSpindel data: {e}") from e

    @staticmethod
    def validate_bubble_sensor(data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate bubble sensor message."""
        try:
            # Validate timestamp format
            if "timestamp" in data:
                try:
                    datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
                except ValueError as e:
                    raise ValidationError(f"Invalid timestamp format: {e}") from e

            return BUBBLE_SENSOR_MESSAGE_SCHEMA(data)
        except vol.Error as e:
            raise ValidationError(f"Invalid bubble sensor data: {e}") from e

    @staticmethod
    def validate_temperature(temperature: float) -> bool:
        """Validate temperature reading."""
        return MIN_TEMPERATURE <= temperature <= MAX_TEMPERATURE

    @staticmethod
    def validate_gravity(gravity: float) -> bool:
        """Validate specific gravity reading."""
        return MIN_GRAVITY <= gravity <= MAX_GRAVITY

    @staticmethod
    def validate_battery(battery: float) -> bool:
        """Validate battery voltage."""
        return MIN_BATTERY <= battery <= MAX_BATTERY

    @staticmethod
    def validate_angle(angle: float) -> bool:
        """Validate angle reading."""
        return MIN_ANGLE <= angle <= MAX_ANGLE

    @staticmethod
    def validate_rssi(rssi: int) -> bool:
        """Validate RSSI signal strength."""
        return MIN_RSSI <= rssi <= MAX_RSSI

    @staticmethod
    def validate_all(data: Dict[str, Any]) -> bool:
        """Validate all sensor fields."""
        validators = {
            "temperature": SensorDataValidator.validate_temperature,
            "gravity": SensorDataValidator.validate_gravity,
            "specific_gravity": SensorDataValidator.validate_gravity,
            "battery": SensorDataValidator.validate_battery,
            "angle": SensorDataValidator.validate_angle,
            "RSSI": SensorDataValidator.validate_rssi,
            "rssi": SensorDataValidator.validate_rssi,
        }

        for field, validator in validators.items():
            if field in data:
                if not validator(data[field]):
                    return False

        return True


class MQTTMessageValidator:
    """Validates MQTT messages."""

    @staticmethod
    def validate_json_payload(payload: bytes) -> Dict[str, Any]:
        """Validate and parse JSON payload."""
        try:
            data = json.loads(payload.decode("utf-8"))
            if not isinstance(data, dict):
                raise ValidationError("Payload must be a JSON object")
            return data
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {e}") from e
        except UnicodeDecodeError as e:
            raise ValidationError(f"Invalid UTF-8 encoding: {e}") from e

    @staticmethod
    def validate_topic_match(topic: str, pattern: str) -> bool:
        """Validate if topic matches pattern."""
        # Simple wildcard matching
        if pattern == topic:
            return True

        # Single-level wildcard (+)
        if "+" in pattern:
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            if len(pattern_parts) != len(topic_parts):
                return False

            for p, t in zip(pattern_parts, topic_parts):
                if p != "+" and p != t:
                    return False

            return True

        # Multi-level wildcard (#)
        if "#" in pattern:
            prefix = pattern.replace("/#", "")
            return topic.startswith(prefix)

        return False

    @staticmethod
    def extract_device_id(topic: str, pattern: str) -> Optional[str]:
        """Extract device ID from topic based on pattern."""
        if "+" in pattern:
            pattern_parts = pattern.split("/")
            topic_parts = topic.split("/")

            if len(pattern_parts) != len(topic_parts):
                return None

            # Find the position of wildcard
            for i, p in enumerate(pattern_parts):
                if p == "+":
                    return topic_parts[i]

        return None


class BatchValidator:
    """Validates batch data."""

    @staticmethod
    def validate(batch: Dict[str, Any]) -> Dict[str, Any]:
        """Validate batch configuration."""
        try:
            # Validate timestamps
            if "start_date" in batch:
                datetime.fromisoformat(batch["start_date"].replace("Z", "+00:00"))

            if "end_date" in batch and batch["end_date"]:
                datetime.fromisoformat(batch["end_date"].replace("Z", "+00:00"))

            validated = BATCH_SCHEMA(batch)

            # Additional validation: final_gravity should be less than initial_gravity
            if "final_gravity" in validated and "initial_gravity" in validated:
                if validated["final_gravity"] >= validated["initial_gravity"]:
                    raise ValidationError(
                        "Final gravity must be less than initial gravity"
                    )

            return validated
        except vol.Error as e:
            raise ValidationError(f"Invalid batch data: {e}") from e
        except ValueError as e:
            raise ValidationError(f"Invalid date format: {e}") from e


class SanityChecker:
    """Performs sanity checks on sensor data."""

    @staticmethod
    def check_gravity_trend(
        readings: List[Dict[str, Any]],
        tolerance: float = 0.020
    ) -> bool:
        """Check if gravity trend is reasonable (should decrease over time)."""
        if len(readings) < 2:
            return True

        # Sort by timestamp
        sorted_readings = sorted(
            readings,
            key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00"))
        )

        # Check for sudden increases
        for i in range(1, len(sorted_readings)):
            current = sorted_readings[i]["gravity"]
            previous = sorted_readings[i - 1]["gravity"]

            # Gravity should not increase significantly
            if current > previous + tolerance:
                return False

        return True

    @staticmethod
    def check_temperature_stability(
        readings: List[Dict[str, Any]],
        max_variance: float = 10.0
    ) -> bool:
        """Check if temperature is relatively stable."""
        if len(readings) < 2:
            return True

        temperatures = [r["temperature"] for r in readings]
        temp_range = max(temperatures) - min(temperatures)

        return temp_range <= max_variance

    @staticmethod
    def check_battery_degradation(
        readings: List[Dict[str, Any]]
    ) -> bool:
        """Check if battery voltage follows expected degradation pattern."""
        if len(readings) < 2:
            return True

        sorted_readings = sorted(
            readings,
            key=lambda x: datetime.fromisoformat(x["timestamp"].replace("Z", "+00:00"))
        )

        # Battery should not increase over time
        for i in range(1, len(sorted_readings)):
            if "battery" not in sorted_readings[i]:
                continue

            current = sorted_readings[i]["battery"]
            previous = sorted_readings[i - 1]["battery"]

            # Small tolerance for measurement error
            if current > previous + 0.1:
                return False

        return True

    @staticmethod
    def check_bubble_rate_lifecycle(
        readings: List[Dict[str, Any]]
    ) -> bool:
        """Check if bubble rate follows expected fermentation lifecycle."""
        if len(readings) < 3:
            return True

        bubble_rates = [r.get("bubble_rate", 0) for r in readings]

        # Should have some variation (not all the same)
        if len(set(bubble_rates)) == 1:
            return len(bubble_rates) <= 2

        return True

    @staticmethod
    def detect_anomalies(
        reading: Dict[str, Any],
        historical_data: List[Dict[str, Any]],
        std_threshold: float = 3.0
    ) -> List[str]:
        """Detect anomalies using statistical methods."""
        if len(historical_data) < 5:
            return []

        anomalies = []

        # Check temperature
        if "temperature" in reading:
            temps = [r["temperature"] for r in historical_data if "temperature" in r]
            if temps:
                mean = sum(temps) / len(temps)
                variance = sum((t - mean) ** 2 for t in temps) / len(temps)
                std = variance ** 0.5

                z_score = abs(reading["temperature"] - mean) / (std + 1e-8)
                if z_score > std_threshold:
                    anomalies.append("temperature")

        # Check gravity
        if "gravity" in reading:
            gravities = [r["gravity"] for r in historical_data if "gravity" in r]
            if gravities:
                mean = sum(gravities) / len(gravities)
                variance = sum((g - mean) ** 2 for g in gravities) / len(gravities)
                std = variance ** 0.5

                z_score = abs(reading["gravity"] - mean) / (std + 1e-8)
                if z_score > std_threshold:
                    anomalies.append("gravity")

        return anomalies
