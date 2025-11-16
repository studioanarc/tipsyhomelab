"""
Sensor Registry

Dynamic sensor detection, registration, and management system.
Automatically discovers available sensors from MQTT topics and manages their lifecycle.
"""

import logging
import re
from typing import Dict, Any, Optional, List, Type, Set
from datetime import datetime, timedelta
from collections import defaultdict

from .base_sensor import BaseSensor, SensorStatus
from .bubble_sensor import BubbleSensor
from .ispindel_sensor import ISpindelSensor
from .optional_sensors import (
    GenericSensor,
    PHSensor,
    DissolvedOxygenSensor,
    PressureSensor,
    TemperatureSensor,
    HumiditySensor,
)


class SensorRegistry:
    """
    Central registry for all sensors in the system.

    Handles:
    - Dynamic sensor discovery from MQTT topics
    - Sensor registration and deregistration
    - Sensor health monitoring
    - Topic routing to appropriate sensors
    - Capability aggregation
    """

    # Topic patterns for sensor type detection
    TOPIC_PATTERNS = {
        'bubble': [
            re.compile(r'^sensors?/bubble/([^/]+)'),
            re.compile(r'^homeassistant/sensor/bubble/([^/]+)'),
        ],
        'ispindel': [
            re.compile(r'^ispindel/([^/]+)'),
            re.compile(r'^sensors?/ispindel/([^/]+)'),
        ],
        'ph': [
            re.compile(r'^sensors?/ph/([^/]+)'),
            re.compile(r'^homeassistant/sensor/ph/([^/]+)'),
        ],
        'dissolved_oxygen': [
            re.compile(r'^sensors?/(?:do|dissolved_oxygen)/([^/]+)'),
        ],
        'pressure': [
            re.compile(r'^sensors?/pressure/([^/]+)'),
        ],
        'temperature': [
            re.compile(r'^sensors?/temperature/([^/]+)'),
        ],
        'humidity': [
            re.compile(r'^sensors?/humidity/([^/]+)'),
        ],
    }

    # Sensor type to class mapping
    SENSOR_CLASSES: Dict[str, Type[BaseSensor]] = {
        'bubble': BubbleSensor,
        'ispindel': ISpindelSensor,
        'ph': PHSensor,
        'dissolved_oxygen': DissolvedOxygenSensor,
        'pressure': PressureSensor,
        'temperature': TemperatureSensor,
        'humidity': HumiditySensor,
        'generic': GenericSensor,
    }

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize sensor registry.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger("sensor_registry")

        # Active sensors: sensor_id -> BaseSensor
        self.sensors: Dict[str, BaseSensor] = {}

        # Topic to sensor mapping for efficient routing
        self.topic_routes: Dict[str, str] = {}  # topic -> sensor_id

        # Discovery tracking
        self.discovered_topics: Set[str] = set()
        self.pending_sensors: Dict[str, Dict[str, Any]] = {}  # sensor_id -> discovery_info

        # Pre-configured sensors
        self.predefined_sensors = config.get('sensors', {})

        # Auto-discovery settings
        self.auto_discovery = config.get('auto_discovery', True)
        self.discovery_timeout = config.get('discovery_timeout', 300)  # 5 minutes

        self.logger.info("Initialized SensorRegistry")

        # Register pre-configured sensors
        self._register_predefined_sensors()

    def _register_predefined_sensors(self):
        """Register sensors from configuration."""
        for sensor_id, sensor_config in self.predefined_sensors.items():
            sensor_type = sensor_config.get('type')
            if not sensor_type:
                self.logger.warning(f"No type specified for sensor {sensor_id}, skipping")
                continue

            self.logger.info(f"Registering predefined sensor: {sensor_id} ({sensor_type})")
            self.register_sensor(sensor_id, sensor_type, sensor_config)

    def detect_sensor_type(self, topic: str) -> Optional[tuple[str, str]]:
        """
        Detect sensor type and ID from MQTT topic.

        Args:
            topic: MQTT topic string

        Returns:
            Tuple of (sensor_type, sensor_id) or None if not recognized
        """
        for sensor_type, patterns in self.TOPIC_PATTERNS.items():
            for pattern in patterns:
                match = pattern.match(topic)
                if match:
                    sensor_id = match.group(1)
                    return sensor_type, sensor_id

        return None

    def register_sensor(
        self,
        sensor_id: str,
        sensor_type: str,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseSensor]:
        """
        Register a new sensor.

        Args:
            sensor_id: Unique sensor identifier
            sensor_type: Type of sensor (bubble, ispindel, etc.)
            config: Optional sensor configuration

        Returns:
            Registered sensor instance or None if registration failed
        """
        # Check if sensor already registered
        if sensor_id in self.sensors:
            self.logger.debug(f"Sensor {sensor_id} already registered")
            return self.sensors[sensor_id]

        # Get sensor class
        sensor_class = self.SENSOR_CLASSES.get(sensor_type)
        if not sensor_class:
            self.logger.warning(f"Unknown sensor type: {sensor_type}")
            return None

        try:
            # Create sensor instance
            sensor = sensor_class(sensor_id, config or {})
            self.sensors[sensor_id] = sensor

            # Register topic routes
            for topic_pattern in sensor.get_mqtt_topics():
                self.topic_routes[topic_pattern] = sensor_id

            self.logger.info(f"Registered sensor: {sensor_id} ({sensor_type})")
            self.logger.debug(f"Sensor capabilities: {sensor.get_capabilities()}")

            return sensor

        except Exception as e:
            self.logger.error(f"Failed to register sensor {sensor_id}: {e}", exc_info=True)
            return None

    def unregister_sensor(self, sensor_id: str) -> bool:
        """
        Unregister a sensor.

        Args:
            sensor_id: Sensor identifier

        Returns:
            True if sensor was unregistered, False otherwise
        """
        if sensor_id not in self.sensors:
            self.logger.warning(f"Sensor {sensor_id} not found in registry")
            return False

        sensor = self.sensors[sensor_id]

        # Remove topic routes
        topics_to_remove = [
            topic for topic, sid in self.topic_routes.items() if sid == sensor_id
        ]
        for topic in topics_to_remove:
            del self.topic_routes[topic]

        # Remove sensor
        del self.sensors[sensor_id]

        self.logger.info(f"Unregistered sensor: {sensor_id}")
        return True

    def process_message(self, topic: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process incoming MQTT message by routing to appropriate sensor.

        Args:
            topic: MQTT topic
            payload: Message payload (JSON decoded)

        Returns:
            Processed sensor data or None
        """
        # Track discovered topics
        if topic not in self.discovered_topics:
            self.discovered_topics.add(topic)
            self._handle_new_topic(topic)

        # Find matching sensor
        sensor_id = self._find_sensor_for_topic(topic)

        if not sensor_id:
            self.logger.debug(f"No sensor registered for topic: {topic}")
            return None

        sensor = self.sensors.get(sensor_id)
        if not sensor:
            self.logger.warning(f"Sensor {sensor_id} not found for topic {topic}")
            return None

        # Process message through sensor
        return sensor.process_message(topic, payload)

    def _handle_new_topic(self, topic: str):
        """
        Handle discovery of new topic.

        Args:
            topic: Newly discovered MQTT topic
        """
        if not self.auto_discovery:
            return

        # Try to detect sensor type
        detection = self.detect_sensor_type(topic)
        if not detection:
            self.logger.debug(f"Could not detect sensor type for topic: {topic}")
            return

        sensor_type, sensor_id = detection

        # Check if sensor already exists
        if sensor_id in self.sensors:
            return

        # Check if sensor is pending
        if sensor_id in self.pending_sensors:
            return

        # Add to pending sensors
        self.pending_sensors[sensor_id] = {
            'sensor_type': sensor_type,
            'discovered_at': datetime.now(),
            'topic': topic,
        }

        self.logger.info(f"Discovered new sensor: {sensor_id} ({sensor_type}) on topic {topic}")

        # Auto-register if enabled
        if self.config.get('auto_register', True):
            self.register_sensor(sensor_id, sensor_type)

    def _find_sensor_for_topic(self, topic: str) -> Optional[str]:
        """
        Find sensor ID for given topic.

        Args:
            topic: MQTT topic

        Returns:
            Sensor ID or None
        """
        # Direct match
        if topic in self.topic_routes:
            return self.topic_routes[topic]

        # Pattern match
        for topic_pattern, sensor_id in self.topic_routes.items():
            # Simple wildcard matching
            if '#' in topic_pattern:
                # MQTT multilevel wildcard
                prefix = topic_pattern.split('#')[0]
                if topic.startswith(prefix):
                    return sensor_id
            elif '+' in topic_pattern:
                # MQTT single level wildcard (simplified)
                pattern_parts = topic_pattern.split('/')
                topic_parts = topic.split('/')
                if len(pattern_parts) == len(topic_parts):
                    match = all(
                        p == '+' or p == t
                        for p, t in zip(pattern_parts, topic_parts)
                    )
                    if match:
                        return sensor_id

        return None

    def get_sensor(self, sensor_id: str) -> Optional[BaseSensor]:
        """
        Get sensor by ID.

        Args:
            sensor_id: Sensor identifier

        Returns:
            Sensor instance or None
        """
        return self.sensors.get(sensor_id)

    def get_all_sensors(self) -> Dict[str, BaseSensor]:
        """
        Get all registered sensors.

        Returns:
            Dictionary of sensor_id -> BaseSensor
        """
        return self.sensors.copy()

    def get_sensors_by_type(self, sensor_type: str) -> List[BaseSensor]:
        """
        Get all sensors of a specific type.

        Args:
            sensor_type: Sensor type to filter

        Returns:
            List of matching sensors
        """
        return [
            sensor for sensor in self.sensors.values()
            if sensor.get_capabilities().get('sensor_type') == sensor_type
        ]

    def get_required_sensors(self) -> List[BaseSensor]:
        """
        Get all required sensors.

        Returns:
            List of required sensors
        """
        return [sensor for sensor in self.sensors.values() if sensor.is_required()]

    def check_required_sensors(self) -> tuple[bool, List[str]]:
        """
        Check if all required sensors are online.

        Returns:
            Tuple of (all_online, missing_sensors)
        """
        required = self.get_required_sensors()
        missing = []

        for sensor in required:
            if sensor.status != SensorStatus.ONLINE:
                missing.append(sensor.sensor_id)

        return len(missing) == 0, missing

    def get_health_summary(self) -> Dict[str, Any]:
        """
        Get health summary for all sensors.

        Returns:
            Dictionary with overall health status
        """
        total = len(self.sensors)
        online = sum(1 for s in self.sensors.values() if s.status == SensorStatus.ONLINE)
        offline = sum(1 for s in self.sensors.values() if s.status == SensorStatus.OFFLINE)
        degraded = sum(1 for s in self.sensors.values() if s.status == SensorStatus.DEGRADED)
        unknown = sum(1 for s in self.sensors.values() if s.status == SensorStatus.UNKNOWN)

        required_online, missing_required = self.check_required_sensors()

        # Get sensor details
        sensor_details = {}
        for sensor_id, sensor in self.sensors.items():
            sensor_details[sensor_id] = sensor.get_health_report()

        return {
            'total_sensors': total,
            'online': online,
            'offline': offline,
            'degraded': degraded,
            'unknown': unknown,
            'required_online': required_online,
            'missing_required': missing_required,
            'sensors': sensor_details,
            'discovered_topics': len(self.discovered_topics),
            'pending_sensors': len(self.pending_sensors),
        }

    def get_capabilities_summary(self) -> Dict[str, Any]:
        """
        Get aggregated capabilities from all sensors.

        Returns:
            Dictionary with system-wide capabilities
        """
        all_measurements = set()
        sensor_types = defaultdict(int)
        measurement_units = {}

        for sensor in self.sensors.values():
            capabilities = sensor.get_capabilities()
            sensor_type = capabilities.get('sensor_type')
            sensor_types[sensor_type] += 1

            measurements = capabilities.get('measurements', [])
            all_measurements.update(measurements)

            units = capabilities.get('units', {})
            measurement_units.update(units)

        return {
            'available_measurements': sorted(list(all_measurements)),
            'sensor_types': dict(sensor_types),
            'measurement_units': measurement_units,
            'total_sensors': len(self.sensors),
        }

    def get_all_topics(self) -> List[str]:
        """
        Get all MQTT topics to subscribe to.

        Returns:
            List of topic patterns
        """
        topics = set()
        for sensor in self.sensors.values():
            topics.update(sensor.get_mqtt_topics())

        # Add discovery topics if auto-discovery enabled
        if self.auto_discovery:
            topics.update([
                'sensors/+/+',
                'sensors/+/+/#',
                'ispindel/+',
                'homeassistant/sensor/+/+/state',
            ])

        return sorted(list(topics))

    def cleanup_stale_sensors(self, timeout_hours: int = 24):
        """
        Remove sensors that haven't been seen in a long time.

        Args:
            timeout_hours: Hours of inactivity before removal
        """
        to_remove = []
        cutoff_time = datetime.now() - timedelta(hours=timeout_hours)

        for sensor_id, sensor in self.sensors.items():
            if sensor.last_seen and sensor.last_seen < cutoff_time:
                if not sensor.is_required():  # Never remove required sensors
                    to_remove.append(sensor_id)

        for sensor_id in to_remove:
            self.logger.info(f"Removing stale sensor: {sensor_id}")
            self.unregister_sensor(sensor_id)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize registry to dictionary.

        Returns:
            Dictionary representation
        """
        return {
            'sensors': {sid: sensor.to_dict() for sid, sensor in self.sensors.items()},
            'health': self.get_health_summary(),
            'capabilities': self.get_capabilities_summary(),
            'auto_discovery': self.auto_discovery,
            'discovered_topics': sorted(list(self.discovered_topics)),
        }
