"""
iSpindel Sensor

Wireless hydrometer for monitoring specific gravity, temperature, and tilt angle
during fermentation. Commonly used in homebrewing and wine making.

iSpindel project: https://github.com/universam1/iSpindel
"""

from datetime import datetime
from typing import Dict, Any, Optional, List
from .base_sensor import BaseSensor, DataQuality
import math


class ISpindelSensor(BaseSensor):
    """
    iSpindel wireless hydrometer sensor implementation.

    Monitors:
    - Specific gravity (SG)
    - Temperature
    - Tilt angle
    - Battery voltage
    - Signal strength (RSSI)

    Standard iSpindel JSON format:
    {
        "name": "iSpindel000",
        "ID": 123456,
        "token": "secret",
        "angle": 45.67,
        "temperature": 20.5,
        "temp_units": "C",
        "battery": 3.8,
        "gravity": 1.050,
        "interval": 900,
        "RSSI": -65
    }
    """

    # Validation thresholds
    MIN_GRAVITY = 0.950  # Typical wine range
    MAX_GRAVITY = 1.150
    MIN_TEMPERATURE = 0.0  # °C
    MAX_TEMPERATURE = 40.0
    MIN_BATTERY = 3.0  # Volts
    MAX_BATTERY = 4.5
    MIN_TILT = 0.0  # degrees
    MAX_TILT = 90.0
    MIN_RSSI = -120  # dBm
    MAX_RSSI = 0

    def __init__(self, sensor_id: str, config: Optional[Dict[str, Any]] = None):
        """
        Initialize iSpindel sensor.

        Args:
            sensor_id: Unique sensor identifier (typically iSpindel name)
            config: Optional configuration including:
                - timeout_seconds: Sensor timeout (default: 1800 = 30 min)
                - polynomial: Calibration polynomial coefficients for tilt->SG conversion
                - expected_interval: Expected update interval (default: 900 = 15 min)
        """
        # iSpindel typically updates every 15 minutes
        if config is None:
            config = {}
        config.setdefault('timeout_seconds', 1800)
        config.setdefault('expected_interval', 900)

        super().__init__(sensor_id, config)

        # Calibration polynomial for tilt angle to specific gravity conversion
        # Format: [a0, a1, a2, a3] where SG = a0 + a1*x + a2*x^2 + a3*x^3
        self.polynomial = config.get('polynomial', None)

        # Track previous values for validation
        self.previous_gravity: Optional[float] = None
        self.previous_temperature: Optional[float] = None

    def get_capabilities(self) -> Dict[str, Any]:
        """Return iSpindel sensor capabilities."""
        return {
            'sensor_type': 'ispindel',
            'required': False,  # Optional but very useful sensor
            'measurements': ['gravity', 'temperature', 'tilt', 'battery', 'rssi'],
            'units': {
                'gravity': 'specific_gravity',
                'temperature': 'celsius',
                'tilt': 'degrees',
                'battery': 'volts',
                'rssi': 'dBm',
            },
            'update_interval': self.config.get('expected_interval', 900),
            'description': 'iSpindel wireless hydrometer',
            'metadata': {
                'has_calibration': self.polynomial is not None,
                'battery_powered': True,
                'wireless': True,
            }
        }

    def parse_message(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse iSpindel message.

        Args:
            payload: Raw MQTT message payload in iSpindel format

        Returns:
            Normalized sensor data

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # iSpindel doesn't always include timestamp, use current time
        timestamp = datetime.now()

        # Extract tilt angle (required)
        angle = payload.get('angle')
        if angle is None:
            raise ValueError("Missing required field: 'angle'")

        try:
            tilt = float(angle)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid tilt angle: {angle}")

        # Extract temperature (required)
        temperature = payload.get('temperature')
        if temperature is None:
            raise ValueError("Missing required field: 'temperature'")

        try:
            temp_value = float(temperature)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid temperature: {temperature}")

        # Check temperature units (convert Fahrenheit to Celsius if needed)
        temp_units = payload.get('temp_units', 'C')
        if temp_units == 'F':
            temp_value = (temp_value - 32) * 5.0 / 9.0

        # Extract gravity
        gravity = payload.get('gravity')
        if gravity is not None:
            try:
                gravity_value = float(gravity)
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid gravity value: {gravity}, will calculate from tilt")
                gravity_value = self._calculate_gravity(tilt)
        else:
            # Calculate gravity from tilt if not provided
            gravity_value = self._calculate_gravity(tilt)

        # Extract battery voltage (required for health monitoring)
        battery = payload.get('battery')
        if battery is None:
            raise ValueError("Missing required field: 'battery'")

        try:
            battery_voltage = float(battery)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid battery voltage: {battery}")

        # Extract optional RSSI
        rssi = None
        if 'RSSI' in payload:
            try:
                rssi = int(payload['RSSI'])
            except (ValueError, TypeError):
                self.logger.warning(f"Invalid RSSI value: {payload['RSSI']}")

        # Extract interval
        interval = payload.get('interval', self.config.get('expected_interval', 900))
        try:
            interval = int(interval)
        except (ValueError, TypeError):
            interval = 900

        # Extract device info
        device_name = payload.get('name', self.sensor_id)
        device_id = payload.get('ID')

        # Build measurements
        measurements = {
            'gravity': round(gravity_value, 4),
            'temperature': round(temp_value, 2),
            'tilt': round(tilt, 2),
            'battery': round(battery_voltage, 2),
        }

        if rssi is not None:
            measurements['rssi'] = rssi

        # Calculate derived measurements
        if self.previous_gravity is not None:
            gravity_change = gravity_value - self.previous_gravity
            measurements['gravity_change'] = round(gravity_change, 4)

        if self.previous_temperature is not None:
            temp_change = temp_value - self.previous_temperature
            measurements['temperature_change'] = round(temp_change, 2)

        # Update previous values
        self.previous_gravity = gravity_value
        self.previous_temperature = temp_value

        # Calculate estimated ABV (if gravity dropped from typical starting point)
        # Assuming typical wine starting gravity of ~1.090
        estimated_abv = None
        if gravity_value < 1.000:
            # Very rough estimate: (OG - FG) * 131.25
            estimated_abv = (1.090 - gravity_value) * 131.25
            measurements['estimated_abv'] = round(estimated_abv, 2)

        return {
            'timestamp': timestamp.isoformat(),
            'sensor_id': self.sensor_id,
            'sensor_type': 'ispindel',
            'measurements': measurements,
            'metadata': {
                'device_name': device_name,
                'device_id': device_id,
                'interval_seconds': interval,
                'temp_units_original': temp_units,
                'has_calibration': self.polynomial is not None,
            }
        }

    def _calculate_gravity(self, tilt: float) -> float:
        """
        Calculate specific gravity from tilt angle using calibration polynomial.

        Args:
            tilt: Tilt angle in degrees

        Returns:
            Specific gravity (SG)
        """
        if self.polynomial is None:
            # If no calibration, return a reasonable estimate
            # This is a rough approximation and should be calibrated
            self.logger.warning("No calibration polynomial configured, using rough estimate")
            # Rough estimate: 25° = 1.090, 60° = 1.000
            return 1.090 - ((tilt - 25) / 35) * 0.090

        # Calculate using polynomial: SG = a0 + a1*x + a2*x^2 + a3*x^3 + ...
        gravity = 0.0
        for power, coeff in enumerate(self.polynomial):
            gravity += coeff * (tilt ** power)

        return gravity

    def validate_data(self, data: Dict[str, Any]) -> tuple[bool, DataQuality, Optional[str]]:
        """
        Validate iSpindel sensor data.

        Args:
            data: Parsed sensor data

        Returns:
            Tuple of (is_valid, quality, error_message)
        """
        measurements = data.get('measurements', {})

        # Check for required measurements
        required = ['gravity', 'temperature', 'tilt', 'battery']
        for field in required:
            if field not in measurements:
                return False, DataQuality.INVALID, f"Missing required measurement: {field}"

        gravity = measurements['gravity']
        temperature = measurements['temperature']
        tilt = measurements['tilt']
        battery = measurements['battery']

        # Validate gravity range
        if gravity < self.MIN_GRAVITY or gravity > self.MAX_GRAVITY:
            return False, DataQuality.INVALID, f"Gravity {gravity} out of valid range [{self.MIN_GRAVITY}, {self.MAX_GRAVITY}]"

        # Validate temperature range
        if temperature < self.MIN_TEMPERATURE or temperature > self.MAX_TEMPERATURE:
            return False, DataQuality.INVALID, f"Temperature {temperature}°C out of valid range"

        # Validate tilt range
        if tilt < self.MIN_TILT or tilt > self.MAX_TILT:
            return False, DataQuality.INVALID, f"Tilt {tilt}° out of valid range"

        # Validate battery
        if battery < self.MIN_BATTERY or battery > self.MAX_BATTERY:
            # Low battery is a warning, not invalid data
            if battery < self.MIN_BATTERY:
                return True, DataQuality.POOR, f"Low battery: {battery}V"
            else:
                return False, DataQuality.INVALID, f"Battery {battery}V out of valid range"

        # Validate RSSI if present
        if 'rssi' in measurements:
            rssi = measurements['rssi']
            if rssi < self.MIN_RSSI or rssi > self.MAX_RSSI:
                return True, DataQuality.ACCEPTABLE, f"RSSI {rssi} dBm out of typical range"

        # Check for unrealistic changes
        if 'gravity_change' in measurements:
            gravity_change = abs(measurements['gravity_change'])
            # Gravity shouldn't change more than 0.020 in 15 minutes during normal fermentation
            max_change = 0.020
            if gravity_change > max_change:
                return True, DataQuality.POOR, f"Unusually large gravity change: {gravity_change}"

        # Assess overall quality
        quality = DataQuality.GOOD

        # Downgrade quality for warning conditions
        if battery < 3.3:
            quality = DataQuality.ACCEPTABLE  # Battery getting low

        if 'rssi' in measurements and measurements['rssi'] < -85:
            quality = DataQuality.ACCEPTABLE  # Weak signal

        return True, quality, None

    def get_mqtt_topics(self) -> List[str]:
        """
        Get MQTT topics for iSpindel.

        iSpindel can publish to various topic formats depending on configuration.

        Returns:
            List of topic patterns
        """
        return [
            f"ispindel/{self.sensor_id}",
            f"ispindel/{self.sensor_id}/tilt",
            f"sensors/ispindel/{self.sensor_id}",
            f"sensors/ispindel/{self.sensor_id}/#",
        ]

    def get_battery_percentage(self) -> Optional[float]:
        """
        Estimate battery percentage from voltage.

        LiPo battery: 4.2V (100%) to 3.0V (0%)

        Returns:
            Estimated battery percentage (0-100) or None
        """
        if not self.last_value:
            return None

        voltage = self.last_value.get('measurements', {}).get('battery')
        if voltage is None:
            return None

        # LiPo discharge curve approximation
        if voltage >= 4.2:
            return 100.0
        elif voltage <= 3.0:
            return 0.0
        else:
            # Simple linear approximation (actual curve is non-linear)
            percentage = ((voltage - 3.0) / (4.2 - 3.0)) * 100.0
            return round(percentage, 1)

    def is_battery_low(self, threshold_voltage: float = 3.3) -> bool:
        """
        Check if battery is low.

        Args:
            threshold_voltage: Voltage threshold for low battery warning

        Returns:
            True if battery is low, False otherwise
        """
        if not self.last_value:
            return False

        voltage = self.last_value.get('measurements', {}).get('battery')
        if voltage is None:
            return False

        return voltage < threshold_voltage

    def get_fermentation_stage(self) -> Optional[str]:
        """
        Estimate fermentation stage based on gravity.

        Returns:
            Estimated stage: 'pre_fermentation', 'active', 'slowing', 'complete', or None
        """
        if not self.last_value:
            return None

        gravity = self.last_value.get('measurements', {}).get('gravity')
        if gravity is None:
            return None

        # Wine typical ranges
        if gravity >= 1.050:
            return 'pre_fermentation'  # High sugar, not started
        elif gravity >= 1.020:
            return 'active'  # Active fermentation
        elif gravity >= 1.000:
            return 'slowing'  # Fermentation slowing down
        else:
            return 'complete'  # Fermentation likely complete

    def set_calibration(self, polynomial: List[float]):
        """
        Set calibration polynomial coefficients.

        Args:
            polynomial: List of coefficients [a0, a1, a2, a3, ...]
        """
        self.polynomial = polynomial
        self.logger.info(f"Updated calibration polynomial: {polynomial}")
