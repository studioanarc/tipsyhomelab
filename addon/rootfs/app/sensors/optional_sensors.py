"""
Optional Sensors

Collection of optional sensor implementations for advanced wine production monitoring.
These sensors are not required but provide valuable additional data.
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from .base_sensor import BaseSensor, DataQuality


class GenericSensor(BaseSensor):
    """
    Generic sensor implementation for simple numeric measurements.

    Useful for any basic sensor that reports a single value with optional metadata.
    Highly flexible and configurable.

    Message Format:
    {
        "timestamp": "2025-11-16T10:30:00Z",  # Optional
        "value": 42.5,                         # Required
        "unit": "unit_name",                   # Optional
        "quality": "good",                     # Optional
        ...additional fields...
    }
    """

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize generic sensor.

        Args:
            sensor_id: Unique sensor identifier
            config: Configuration including:
                - measurement_name: Name of the measurement (e.g., 'pressure')
                - unit: Unit of measurement
                - min_value: Minimum valid value
                - max_value: Maximum valid value
                - timeout_seconds: Sensor timeout
        """
        super().__init__(sensor_id, config)

        self.measurement_name = config.get('measurement_name', 'value')
        self.unit = config.get('unit', 'unknown')
        self.min_value = config.get('min_value', -float('inf'))
        self.max_value = config.get('max_value', float('inf'))

    def get_capabilities(self) -> Dict[str, Any]:
        """Return generic sensor capabilities."""
        return {
            'sensor_type': 'generic',
            'required': False,
            'measurements': [self.measurement_name],
            'units': {
                self.measurement_name: self.unit,
            },
            'update_interval': self.config.get('expected_interval', 60),
            'description': f'Generic {self.measurement_name} sensor',
            'metadata': {
                'min_value': self.min_value,
                'max_value': self.max_value,
            }
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Parse generic sensor message."""
        # Extract timestamp
        timestamp_str = payload.get('timestamp')
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                timestamp = datetime.now()
        else:
            timestamp = datetime.now()

        # Extract value (required)
        value = payload.get('value')
        if value is None:
            raise ValueError("Missing required field: 'value'")

        try:
            numeric_value = float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid value: {value}")

        # Build measurements
        measurements = {
            self.measurement_name: numeric_value,
        }

        # Include any additional fields from payload
        metadata = {}
        for key, val in payload.items():
            if key not in ['timestamp', 'value']:
                metadata[key] = val

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'generic',
            'measurements': measurements,
            'metadata': metadata,
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        """Validate generic sensor data."""
        measurements = data.get('measurements', {})

        if self.measurement_name not in measurements:
            return False, DataQuality.INVALID, f"Missing measurement: {self.measurement_name}"

        value = measurements[self.measurement_name]

        # Check range
        if value < self.min_value:
            return False, DataQuality.INVALID, f"Value {value} below minimum {self.min_value}"

        if value > self.max_value:
            return False, DataQuality.INVALID, f"Value {value} above maximum {self.max_value}"

        return True, DataQuality.GOOD, None


class PHSensor(BaseSensor):
    """
    pH sensor for wine acidity monitoring.

    Wine pH typically ranges from 3.0 to 4.0.
    """

    MIN_PH = 0.0
    MAX_PH = 14.0
    WINE_MIN_PH = 2.8
    WINE_MAX_PH = 4.2

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'ph',
            'required': False,
            'measurements': ['ph'],
            'units': {'ph': 'pH'},
            'update_interval': self.config.get('expected_interval', 300),
            'description': 'pH sensor for acidity monitoring',
            'metadata': {
                'ideal_wine_range': [self.WINE_MIN_PH, self.WINE_MAX_PH],
            }
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = payload.get('timestamp')
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        # Accept 'ph', 'pH', or 'value'
        ph_value = payload.get('ph') or payload.get('pH') or payload.get('value')
        if ph_value is None:
            raise ValueError("Missing pH value")

        try:
            ph = float(ph_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid pH value: {ph_value}")

        # Extract optional temperature (pH is temperature dependent)
        temperature = None
        if 'temperature' in payload:
            try:
                temperature = float(payload['temperature'])
            except (ValueError, TypeError):
                pass

        measurements = {'ph': round(ph, 2)}
        if temperature is not None:
            measurements['temperature'] = round(temperature, 2)

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'ph',
            'measurements': measurements,
            'metadata': {
                'temperature_compensated': 'temperature' in payload,
            }
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        measurements = data.get('measurements', {})

        if 'ph' not in measurements:
            return False, DataQuality.INVALID, "Missing pH measurement"

        ph = measurements['ph']

        if ph < self.MIN_PH or ph > self.MAX_PH:
            return False, DataQuality.INVALID, f"pH {ph} out of valid range [0, 14]"

        # Assess quality based on wine range
        if ph < self.WINE_MIN_PH or ph > self.WINE_MAX_PH:
            return True, DataQuality.ACCEPTABLE, f"pH {ph} outside typical wine range"

        return True, DataQuality.GOOD, None


class DissolvedOxygenSensor(BaseSensor):
    """
    Dissolved Oxygen (DO) sensor.

    Important for monitoring oxidation risk during wine production.
    """

    MIN_DO = 0.0  # mg/L
    MAX_DO = 20.0  # mg/L

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'dissolved_oxygen',
            'required': False,
            'measurements': ['dissolved_oxygen'],
            'units': {'dissolved_oxygen': 'mg/L'},
            'update_interval': self.config.get('expected_interval', 300),
            'description': 'Dissolved oxygen sensor',
            'metadata': {
                'ideal_range': [0.0, 2.0],  # Low DO is desirable for wine
            }
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = payload.get('timestamp')
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        do_value = payload.get('do') or payload.get('dissolved_oxygen') or payload.get('value')
        if do_value is None:
            raise ValueError("Missing dissolved oxygen value")

        try:
            do = float(do_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid DO value: {do_value}")

        measurements = {'dissolved_oxygen': round(do, 2)}

        # Optional temperature and pressure for compensation
        if 'temperature' in payload:
            try:
                measurements['temperature'] = round(float(payload['temperature']), 2)
            except (ValueError, TypeError):
                pass

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'dissolved_oxygen',
            'measurements': measurements,
            'metadata': {}
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        measurements = data.get('measurements', {})

        if 'dissolved_oxygen' not in measurements:
            return False, DataQuality.INVALID, "Missing DO measurement"

        do = measurements['dissolved_oxygen']

        if do < self.MIN_DO or do > self.MAX_DO:
            return False, DataQuality.INVALID, f"DO {do} mg/L out of valid range"

        # High DO is a warning for wine (oxidation risk)
        if do > 5.0:
            return True, DataQuality.ACCEPTABLE, f"High DO level: {do} mg/L (oxidation risk)"

        return True, DataQuality.GOOD, None


class PressureSensor(BaseSensor):
    """
    Pressure sensor for monitoring fermentation vessel pressure.

    Useful for closed fermentation systems.
    """

    MIN_PRESSURE = 0.0  # PSI (absolute)
    MAX_PRESSURE = 50.0  # PSI

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)
        self.unit = config.get('unit', 'psi') if config else 'psi'

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'pressure',
            'required': False,
            'measurements': ['pressure'],
            'units': {'pressure': self.unit},
            'update_interval': self.config.get('expected_interval', 60),
            'description': 'Pressure sensor',
            'metadata': {}
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = payload.get('timestamp')
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        pressure_value = payload.get('pressure') or payload.get('value')
        if pressure_value is None:
            raise ValueError("Missing pressure value")

        try:
            pressure = float(pressure_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid pressure value: {pressure_value}")

        measurements = {'pressure': round(pressure, 2)}

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'pressure',
            'measurements': measurements,
            'metadata': {'unit': self.unit}
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        measurements = data.get('measurements', {})

        if 'pressure' not in measurements:
            return False, DataQuality.INVALID, "Missing pressure measurement"

        pressure = measurements['pressure']

        if pressure < self.MIN_PRESSURE or pressure > self.MAX_PRESSURE:
            return False, DataQuality.INVALID, f"Pressure {pressure} out of valid range"

        # High pressure warning
        if pressure > 30.0:
            return True, DataQuality.ACCEPTABLE, f"High pressure: {pressure} {self.unit}"

        return True, DataQuality.GOOD, None


class TemperatureSensor(BaseSensor):
    """
    Standalone temperature sensor.

    For ambient or additional temperature monitoring beyond fermentation vessel.
    """

    MIN_TEMP = -20.0  # °C
    MAX_TEMP = 60.0   # °C

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'temperature',
            'required': False,
            'measurements': ['temperature'],
            'units': {'temperature': 'celsius'},
            'update_interval': self.config.get('expected_interval', 60),
            'description': 'Temperature sensor',
            'metadata': {}
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = payload.get('timestamp')
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        temp_value = payload.get('temperature') or payload.get('value')
        if temp_value is None:
            raise ValueError("Missing temperature value")

        try:
            temperature = float(temp_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid temperature value: {temp_value}")

        measurements = {'temperature': round(temperature, 2)}

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'temperature',
            'measurements': measurements,
            'metadata': {}
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        measurements = data.get('measurements', {})

        if 'temperature' not in measurements:
            return False, DataQuality.INVALID, "Missing temperature measurement"

        temperature = measurements['temperature']

        if temperature < self.MIN_TEMP or temperature > self.MAX_TEMP:
            return False, DataQuality.INVALID, f"Temperature {temperature}°C out of valid range"

        return True, DataQuality.GOOD, None


class HumiditySensor(BaseSensor):
    """
    Humidity sensor for monitoring storage conditions.
    """

    MIN_HUMIDITY = 0.0    # %
    MAX_HUMIDITY = 100.0  # %

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(sensor_id, config)

    def get_capabilities(self) -> Dict[str, Any]:
        return {
            'sensor_type': 'humidity',
            'required': False,
            'measurements': ['humidity'],
            'units': {'humidity': 'percent'},
            'update_interval': self.config.get('expected_interval', 60),
            'description': 'Humidity sensor',
            'metadata': {}
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        timestamp_str = payload.get('timestamp')
        timestamp = datetime.now()
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass

        humidity_value = payload.get('humidity') or payload.get('value')
        if humidity_value is None:
            raise ValueError("Missing humidity value")

        try:
            humidity = float(humidity_value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid humidity value: {humidity_value}")

        measurements = {'humidity': round(humidity, 1)}

        # Include temperature if available (often combined sensor)
        if 'temperature' in payload:
            try:
                measurements['temperature'] = round(float(payload['temperature']), 2)
            except (ValueError, TypeError):
                pass

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'humidity',
            'measurements': measurements,
            'metadata': {}
        }

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        measurements = data.get('measurements', {})

        if 'humidity' not in measurements:
            return False, DataQuality.INVALID, "Missing humidity measurement"

        humidity = measurements['humidity']

        if humidity < self.MIN_HUMIDITY or humidity > self.MAX_HUMIDITY:
            return False, DataQuality.INVALID, f"Humidity {humidity}% out of valid range"

        return True, DataQuality.GOOD, None
