"""
Bubble Counter Sensor

Monitors CO2 bubble production during fermentation.
This is a REQUIRED sensor for the wine production monitoring system.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from .base_sensor import BaseSensor, DataQuality


class BubbleSensor(BaseSensor):
    """
    CO2 bubble counter sensor implementation.

    Tracks fermentation activity by counting CO2 bubbles produced.
    This is the primary indicator of active fermentation.

    Message Format (flexible):
    {
        "timestamp": "2025-11-16T10:30:00Z",  # Optional, will use current time if missing
        "bubbles": 42,                         # Total bubble count or increment
        "interval": 60,                        # Optional: measurement interval in seconds
        "rate": 0.7,                          # Optional: bubbles per minute
        "temperature": 22.5,                  # Optional: ambient temperature
        "battery": 85,                        # Optional: battery percentage
        "cumulative": true                    # Optional: whether bubbles is cumulative count
    }
    """

    # Validation thresholds
    MIN_BUBBLE_RATE = 0.0  # bubbles/min
    MAX_BUBBLE_RATE = 300.0  # bubbles/min (sanity check)
    MIN_TEMPERATURE = -10.0  # °C
    MAX_TEMPERATURE = 50.0  # °C
    MIN_INTERVAL = 1  # seconds
    MAX_INTERVAL = 3600  # seconds

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize bubble counter sensor.

        Args:
            sensor_id: Unique sensor identifier
            config: Optional configuration including:
                - timeout_seconds: Sensor timeout (default: 300)
                - expected_interval: Expected update interval (default: 60)
                - cumulative_mode: Whether sensor sends cumulative counts
        """
        super().__init__(sensor_id, config)

        # Bubble counting state
        self.last_bubble_count: Optional[int] = None
        self.cumulative_mode = config.get('cumulative_mode', True)
        self.total_bubbles = 0

    def get_capabilities(self) -> Dict[str, Any]:
        """Return bubble sensor capabilities."""
        return {
            'sensor_type': 'bubble_counter',
            'required': True,  # This is a REQUIRED sensor
            'measurements': ['bubbles', 'bubble_rate', 'temperature'],
            'units': {
                'bubbles': 'count',
                'bubble_rate': 'bubbles_per_minute',
                'temperature': 'celsius',
            },
            'update_interval': self.config.get('expected_interval', 60),
            'description': 'CO2 bubble counter for fermentation monitoring',
            'metadata': {
                'cumulative_mode': self.cumulative_mode,
                'primary_measurement': 'bubble_rate',
            }
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse bubble counter message.

        Args:
            payload: Raw MQTT message payload

        Returns:
            Normalized sensor data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Extract timestamp
        timestamp_str = payload.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Extract bubble count (required)
        bubbles = payload.get('bubbles')
        if bubbles is None:
            raise ValueError("Missing required field: 'bubbles'")

        try:
            bubbles = int(bubbles)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid bubble count: {bubbles}")

        # Check if this is cumulative or incremental
        is_cumulative = payload.get('cumulative', self.cumulative_mode)

        # Calculate bubble increment
        bubble_increment = bubbles
        if is_cumulative and self.last_bubble_count is not None:
            bubble_increment = bubbles - self.last_bubble_count
            # Handle counter reset
            if bubble_increment < 0:
                self.logger.warning(f"Bubble count reset detected: {self.last_bubble_count} -> {bubbles}")
                bubble_increment = bubbles

        if is_cumulative:
            self.last_bubble_count = bubbles

        # Update total
        self.total_bubbles += max(0, bubble_increment)

        # Extract interval
        interval = payload.get('interval', self.config.get('expected_interval', 60))
        try:
            interval = float(interval)
        except (ValueError, TypeError):
            interval = 60.0

        # Calculate or extract bubble rate
        if 'rate' in payload:
            try:
                bubble_rate = float(payload['rate'])
            except (ValueError, TypeError):
                bubble_rate = (bubble_increment / interval) * 60.0 if interval > 0 else 0.0
        else:
            bubble_rate = (bubble_increment / interval) * 60.0 if interval > 0 else 0.0

        # Extract optional temperature
        temperature = None
        if 'temperature' in payload:
            try:
                temperature = float(payload['temperature'])
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid temperature value: {payload['temperature']}")

        # Extract optional battery
        battery = None
        if 'battery' in payload:
            try:
                battery = float(payload['battery'])
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid battery value: {payload['battery']}")

        # Build normalized data structure
        measurements = {
            'bubbles': bubble_increment,
            'bubble_rate': round(bubble_rate, 3),
            'cumulative_bubbles': self.total_bubbles,
        }

        if temperature is not None:
            measurements['temperature'] = round(temperature, 2)

        if battery is not None:
            measurements['battery'] = round(battery, 1)

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'bubble_counter',
            'measurements': measurements,
            'metadata': {
                'interval_seconds': interval,
                'is_cumulative': is_cumulative,
                'raw_count': bubbles,
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        """
        Validate bubble sensor data.

        Args:
            data: Parsed sensor data

        Returns:
            Tuple of (is_valid, quality, error_message)
        """
        measurements = data.get('measurements', {})

        # Check for required measurements
        if 'bubble_rate' not in measurements:
            return False, DataQuality.INVALID, "Missing bubble_rate measurement"

        bubble_rate = measurements['bubble_rate']
        bubbles = measurements.get('bubbles', 0)

        # Validate bubble rate range
        if bubble_rate < self.MIN_BUBBLE_RATE:
            # Zero or slightly negative is acceptable (no fermentation activity)
            quality = DataQuality.ACCEPTABLE if bubble_rate >= -0.1 else DataQuality.POOR
            return True, quality, None

        if bubble_rate > self.MAX_BUBBLE_RATE:
            return False, DataQuality.INVALID, f"Bubble rate {bubble_rate} exceeds maximum {self.MAX_BUBBLE_RATE}"

        # Validate bubble count
        if bubbles < 0:
            return False, DataQuality.INVALID, f"Negative bubble count: {bubbles}"

        # Validate optional temperature if present
        if 'temperature' in measurements:
            temp = measurements['temperature']
            if temp < self.MIN_TEMPERATURE or temp > self.MAX_TEMPERATURE:
                return True, DataQuality.POOR, f"Temperature {temp}°C out of expected range"

        # Validate interval
        interval = data.get('metadata', {}).get('interval_seconds', 60)
        if interval < self.MIN_INTERVAL or interval > self.MAX_INTERVAL:
            return True, DataQuality.POOR, f"Interval {interval}s out of expected range"

        # Assess data quality based on bubble rate
        # Very low or zero bubble rate is acceptable but might indicate inactive fermentation
        if bubble_rate < 0.1:
            quality = DataQuality.ACCEPTABLE
        else:
            quality = DataQuality.GOOD

        return True, quality, None

    def get_mqtt_topics(self) -> List[str]:
        """
        Get MQTT topics for bubble counter.

        Returns:
            List of topic patterns
        """
        return [
            f"sensors/bubble/{self.sensor_id}",
            f"sensors/bubble/{self.sensor_id}/#",
            f"homeassistant/sensor/bubble/{self.sensor_id}/state",
        ]

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get bubble counting statistics.

        Returns:
            Dictionary with statistics
        """
        stats = {
            'total_bubbles': self.total_bubbles,
            'last_count': self.last_bubble_count,
            'cumulative_mode': self.cumulative_mode,
        }

        if self.last_value:
            measurements = self.last_value.get('measurements', {})
            stats['current_rate'] = measurements.get('bubble_rate', 0)
            stats['last_temperature'] = measurements.get('temperature')
            stats['last_battery'] = measurements.get('battery')

        return stats

    def reset_counter(self):
        """Reset the bubble counter (for manual override)."""
        self.logger.info(f"Resetting bubble counter for {self.sensor_id}")
        self.last_bubble_count = None
        self.total_bubbles = 0
